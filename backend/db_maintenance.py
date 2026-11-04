"""Database size report and analytics archiving for the Supabase free tier.

Run these from your own PC (with DATABASE_URL pointing at Supabase), never on
Render: they do the heavy work on your machine and the database, so the 0.1
vCPU web instance is untouched.

    flask --app backend:create_app db-usage
    flask --app backend:create_app analytics-archive --before 2025-11-01            # dry run
    flask --app backend:create_app analytics-archive --before 2025-11-01 --apply    # backup + delete
"""
import csv
import gzip
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, text

from .models import db, AnalyticsEvent, AnalyticsQuestionDay, AnalyticsDaily, AnalyticsReceipt

FREE_TIER_BYTES = 500 * 1024 * 1024
WATCHED = ('attempt_answer', 'attempt', 'question', 'question_option', 'question_image', 'analytics_event',
           'analytics_question_day', 'analytics_daily', 'analytics_receipt', 'ai_solution', 'ingestion_file',
           'contact_message', 'content_report')
MIN_KEEP_DAYS = 180  # Reports chart up to 90 days; keep a generous margin.


def usage():
    """Return total size and per-table size/row counts (largest first)."""
    engine = db.engine
    rows = []
    if engine.dialect.name == 'postgresql':
        total = db.session.execute(text('SELECT pg_database_size(current_database())')).scalar() or 0
        for name in WATCHED:
            size = db.session.execute(text('SELECT pg_total_relation_size(to_regclass(:t))'), {'t': name}).scalar()
            if size is None:
                continue
            count = db.session.execute(text(f'SELECT count(*) FROM "{name}"')).scalar()
            rows.append({'table': name, 'rows': count, 'bytes': int(size)})
    else:
        path = Path(engine.url.database or '')
        total = path.stat().st_size if path.is_file() else 0
        for name in WATCHED:
            try:
                count = db.session.execute(text(f'SELECT count(*) FROM "{name}"')).scalar()
            except Exception:
                db.session.rollback()
                continue
            rows.append({'table': name, 'rows': count, 'bytes': None})
    rows.sort(key=lambda r: (r['bytes'] or 0, r['rows']), reverse=True)
    return {'dialect': engine.dialect.name, 'total_bytes': int(total), 'limit_bytes': FREE_TIER_BYTES, 'tables': rows}


def _cutoff(before):
    try:
        day = datetime.strptime(before, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValueError('Use --before YYYY-MM-DD') from None
    if day > date.today() - timedelta(days=MIN_KEEP_DAYS):
        raise ValueError(f'Keep at least the last {MIN_KEEP_DAYS} days; choose a date on or before '
                         f'{date.today() - timedelta(days=MIN_KEEP_DAYS)}.')
    return day.isoformat()


def _write_csv(path, query, columns):
    count = 0
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in query.yield_per(2000):
            writer.writerow([getattr(row, c) for c in columns])
            count += 1
    return count


def archive(before, apply=False, out_dir='analytics-archive', drop_legacy=False, batch=5000):
    """Back up then delete analytics rows older than `before` (YYYY-MM-DD).

    Dry run by default: only counts. With apply=True every row is first written
    to a gzipped CSV in out_dir, then deleted in small batches. Reports for
    periods before the cutoff will afterwards show no data; current reports are
    unaffected. drop_legacy also empties analytics_daily and analytics_receipt,
    which no current code reads.
    """
    cutoff = _cutoff(before)
    events = AnalyticsEvent.query.filter(AnalyticsEvent.start_day < cutoff)
    days = AnalyticsQuestionDay.query.filter(AnalyticsQuestionDay.day < cutoff)
    plan = {'before': cutoff, 'events': events.count(), 'question_days': days.count(),
            'legacy_daily': AnalyticsDaily.query.count() if drop_legacy else 0,
            'legacy_receipts': AnalyticsReceipt.query.count() if drop_legacy else 0,
            'applied': False, 'files': []}
    if not apply:
        return plan
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    exports = [(events, AnalyticsEvent, 'analytics_event'), (days, AnalyticsQuestionDay, 'analytics_question_day')]
    if drop_legacy:
        exports += [(AnalyticsDaily.query, AnalyticsDaily, 'analytics_daily'), (AnalyticsReceipt.query, AnalyticsReceipt, 'analytics_receipt')]
    for query, model, name in exports:
        columns = [c.name for c in model.__table__.columns]
        path = out / f'{name}-before-{cutoff}-{stamp}.csv.gz'
        written = _write_csv(path, query, columns)
        plan['files'].append({'file': str(path), 'rows': written})
    # Delete only after every backup file is complete.
    _delete_batches(AnalyticsEvent, AnalyticsEvent.key, AnalyticsEvent.start_day < cutoff, batch)
    _delete_where(AnalyticsQuestionDay.__table__.delete().where(AnalyticsQuestionDay.day < cutoff))
    if drop_legacy:
        _delete_where(AnalyticsDaily.__table__.delete())
        _delete_where(AnalyticsReceipt.__table__.delete())
    plan['applied'] = True
    return plan


def _delete_batches(model, key, condition, batch):
    while True:
        keys = [k for k, in db.session.query(key).filter(condition).limit(batch)]
        if not keys:
            return
        db.session.query(model).filter(key.in_(keys)).delete(synchronize_session=False)
        db.session.commit()


def _delete_where(statement):
    db.session.execute(statement)
    db.session.commit()


def human(n):
    if n is None:
        return '—'
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024
