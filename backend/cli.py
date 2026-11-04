import os,json
import click
from werkzeug.security import generate_password_hash
from .models import db,User

def register_cli(app):
    @app.cli.command('check-db')
    def check_db():
        """Read-only connection check. Does not create tables or migrate data."""
        from sqlalchemy import text
        try:
            with db.engine.connect() as connection:
                if connection.dialect.name=='postgresql':connection.execute(text('SET TRANSACTION READ ONLY'))
                assert connection.execute(text('SELECT 1')).scalar_one()==1
                connection.rollback()
            click.echo('Connection OK ('+db.engine.dialect.name+'). Read-only SELECT 1 passed; no schema or data changes.')
        except Exception:
            # Driver errors can include credentials/URLs. Never print their raw text.
            raise click.ClickException('Connection failed. Check DATABASE_URL privately, password URL encoding, SSL settings, and network/IPv4 availability. No migrations were run.') from None

    @app.cli.command('cleanup-sessions')
    def cleanup_sessions_command():
        """Expire timed exams and delete expired temporary responses/results."""
        from .engine import expire_all
        expire_all();click.echo('Expired sessions cleaned; latest paper progress retained.')

    @app.cli.command('db-usage')
    def db_usage():
        """Show database size per table against the Supabase free-tier limit. Read-only."""
        from .db_maintenance import usage,human
        u=usage()
        if u['dialect']=='postgresql':
            pct=100*u['total_bytes']/u['limit_bytes']
            click.echo(f"Database: {human(u['total_bytes'])} of {human(u['limit_bytes'])} free tier ({pct:.1f}%)")
        else:
            click.echo(f"SQLite file: {human(u['total_bytes'])} (per-table sizes are shown for PostgreSQL only)")
        for r in u['tables']:click.echo(f"  {r['table']:<24} {r['rows']:>10,} rows  {human(r['bytes']):>10}")

    @app.cli.command('analytics-archive')
    @click.option('--before',required=True,help='Archive analytics older than this day (YYYY-MM-DD).')
    @click.option('--apply',is_flag=True,help='Write the CSV backup and delete. Without it, only counts are shown.')
    @click.option('--out',default='analytics-archive',show_default=True,help='Folder for the gzipped CSV backups.')
    @click.option('--drop-legacy',is_flag=True,help='Also empty the unused analytics_daily and analytics_receipt tables.')
    def analytics_archive(before,apply,out,drop_legacy):
        """Back up and remove old analytics rows to stay within the free database limit."""
        from .db_maintenance import archive
        try:plan=archive(before,apply=apply,out_dir=out,drop_legacy=drop_legacy)
        except ValueError as exc:raise click.ClickException(str(exc)) from None
        click.echo(f"Analytics before {plan['before']}: {plan['events']:,} usage events, {plan['question_days']:,} question-day rows"+(f", {plan['legacy_daily']:,} legacy daily rows, {plan['legacy_receipts']:,} legacy receipts" if drop_legacy else ''))
        if not plan['applied']:click.echo('Dry run: nothing changed. Add --apply to back up and delete.');return
        for f in plan['files']:click.echo(f"  backup {f['file']} ({f['rows']:,} rows)")
        click.echo('Archived and deleted. Reports for later periods are unchanged.')

    @app.cli.command('init-db')
    def init_db():
        db.create_all();click.echo('Database created. Use flask db upgrade for versioned deployment.')
    @app.cli.command('create-admin')
    @click.option('--email',prompt=True)
    @click.option('--password',prompt=True,hide_input=True,confirmation_prompt=True)
    def create_admin(email,password):
        if len(password)<12:raise click.ClickException('Use at least 12 characters')
        if User.query.filter_by(email=email.lower().strip()).first():raise click.ClickException('Account already exists; no implicit promotion')
        db.session.add(User(email=email.lower().strip(),name='Administrator',password_hash=generate_password_hash(password),role='ADMIN'));db.session.commit();click.echo('Admin created')
    @app.cli.command('import-catalog')
    @click.argument('path',type=click.Path(exists=True))
    def import_catalog(path):
        from .catalog import import_workbook
        report=import_workbook(path)
        from .acquisition import queue_catalog
        batch,count=queue_catalog() if app.config['CATALOG_AUTO_PROCESS'] else (None,0)
        report.update(batch_id=batch,queued=count)
        click.echo(json.dumps(report,indent=2))
    @app.cli.command('repair-catalog-sources')
    @click.argument('path',type=click.Path(exists=True))
    @click.option('--course-code',required=True)
    @click.option('--term',multiple=True,required=True)
    @click.option('--apply',is_flag=True)
    def repair_catalog_sources(path,course_code,term,apply):
        """Preview or queue corrected sources for existing papers only."""
        from .catalog import scan_workbook,compare_scan,code_key
        from .models import Paper
        from .acquisition import queue_catalog
        scan=scan_workbook(path);preview=compare_scan(scan)
        changes=[e for e in preview['items']['changed'] if code_key(e['course_code'])==code_key(course_code) and e['term_name'] in term]
        click.echo(json.dumps([{'paper_id':e['paper_id'],'term':e['term_name'],'exam':e['exam_name'],'name':e['name']} for e in changes],indent=2))
        if not apply:
            click.echo('Preview only; no changes. Use --apply to queue these existing papers.');return
        ids=[e['paper_id'] for e in changes]
        if not ids:click.echo('No source corrections needed.');return
        from .models import IngestionFile
        if IngestionFile.query.filter(IngestionFile.paper_id.in_(ids),IngestionFile.status.in_(['QUEUED','FETCH_QUEUED','FETCHING','PROCESSING'])).first():
            raise click.ClickException('A selected paper is already processing; finish or recover it before repair.')
        for e in changes:
            paper=db.session.get(Paper,e['paper_id'])
            paper.source_url=e['url'];paper.name=e['name']
            # Keep the existing bank (including any alias) until validation succeeds.
        db.session.commit()
        batch,count=queue_catalog(paper_ids=ids,limit=len(ids),force_paper_ids=set(ids))
        click.echo(json.dumps({'batch_id':batch,'queued':count}))

    @app.cli.command('worker')
    @click.option('--once',is_flag=True)
    def worker(once):
        from .ingestion import worker_loop
        worker_loop(once)

    @app.cli.command('populate')
    @click.argument('path',type=click.Path(exists=True))
    @click.option('--retry',is_flag=True)
    def populate(path,retry):
        from .catalog import import_workbook
        from .acquisition import queue_catalog,download_pending
        from .ingestion import work_once
        click.echo(json.dumps(import_workbook(path),indent=2))
        click.echo(f'Queued: {queue_catalog(retry=retry)}')
        download_pending(app,workers=4)
        while work_once():db.session.remove()
        click.echo('All queued sources attempted and processed. See Administration / Processing for exact results.')
