import csv, gzip
from datetime import date, timedelta
import pytest
from backend.models import db, AnalyticsEvent, AnalyticsQuestionDay, AnalyticsDaily


def event(key, day):
    return AnalyticsEvent(key=key, started_at=1.0, start_day=day, browser_key='b'*64, paper_key='p1', paper_name='Paper',
                          course_key='c1', course_name='Course', initial_mode='exam', device='mobile', automatic=False, expires_at=2.0)


def seed():
    old = (date.today() - timedelta(days=400)).isoformat()
    new = (date.today() - timedelta(days=5)).isoformat()
    db.session.add_all([event('old-1', old), event('old-2', old), event('new-1', new),
                        AnalyticsQuestionDay(day=old, paper_key='p1', question_id=1, version='v', mode='exam', number='1', correct=1),
                        AnalyticsQuestionDay(day=new, paper_key='p1', question_id=1, version='v', mode='exam', number='1', correct=2),
                        AnalyticsDaily(day=old, paper_key='p1', mode='exam', device='mobile', paper_name='P', course_key='c1', course_name='C')])
    db.session.commit()
    return (date.today() - timedelta(days=200)).isoformat()


def test_archive_dry_run_changes_nothing(app):
    from backend.db_maintenance import archive
    cutoff = seed()
    plan = archive(cutoff)
    assert plan['events'] == 2 and plan['question_days'] == 1 and not plan['applied']
    assert AnalyticsEvent.query.count() == 3


def test_archive_backs_up_then_deletes_only_old_rows(app, tmp_path):
    from backend.db_maintenance import archive
    cutoff = seed()
    plan = archive(cutoff, apply=True, out_dir=str(tmp_path), drop_legacy=True)
    assert plan['applied']
    assert [e.key for e in AnalyticsEvent.query.all()] == ['new-1']
    assert AnalyticsQuestionDay.query.count() == 1 and AnalyticsDaily.query.count() == 0
    backup = next(f for f in plan['files'] if 'analytics_event' in f['file'])
    with gzip.open(backup['file'], 'rt') as handle:
        rows = list(csv.DictReader(handle))
    assert sorted(r['key'] for r in rows) == ['old-1', 'old-2'] and backup['rows'] == 2


def test_archive_refuses_recent_cutoff(app):
    from backend.db_maintenance import archive
    with pytest.raises(ValueError, match='Keep at least'):
        archive((date.today() - timedelta(days=30)).isoformat())
    with pytest.raises(ValueError, match='YYYY-MM-DD'):
        archive('last year')


def test_cli_commands(app):
    seed()
    runner = app.test_cli_runner()
    out = runner.invoke(args=['db-usage'])
    assert out.exit_code == 0 and 'analytics_event' in out.output
    dry = runner.invoke(args=['analytics-archive', '--before', (date.today() - timedelta(days=200)).isoformat()])
    assert dry.exit_code == 0 and 'Dry run' in dry.output and '2 usage events' in dry.output
    bad = runner.invoke(args=['analytics-archive', '--before', date.today().isoformat()])
    assert bad.exit_code != 0 and 'Keep at least' in bad.output
