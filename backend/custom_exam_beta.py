"""Small, transactional admission counters for public custom exams."""
import math
import time
from datetime import datetime, timedelta, timezone

from flask import current_app, g, jsonify
from sqlalchemy import case, delete, select, update

from .models import Attempt, CustomExamBrowser, CustomExamQuota, db

DAILY_LIMIT = 2500
COOLDOWN_SECONDS = 60
IST = timezone(timedelta(hours=5, minutes=30))


def enabled():
    return current_app.config['CUSTOM_EXAM_BETA_ENABLED']


def day_window(now):
    local = datetime.fromtimestamp(now, IST)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return local.date(), (midnight + timedelta(days=1)).timestamp()


def conflict(code, message, status=409, retry_after=None, **details):
    headers = {}
    if retry_after is not None:
        headers['Retry-After'] = str(retry_after)
        details['retry_after_seconds'] = retry_after
    return jsonify(code=code, error=message, **details), status, headers


def blocked(state, now, questions=1):
    if not enabled() or state.paused:
        return conflict('CUSTOM_PAUSED',
                        'New Custom Exams are temporarily paused. You can still finish an exam you already started.', 503)
    day, reset = day_window(now)
    remaining = DAILY_LIMIT - (state.questions_used if state.day == day else 0)
    if questions > remaining:
        return conflict('CUSTOM_DAILY_QUOTA',
                        'Today’s Custom Exam quota is full.' if not remaining else
                        f'{remaining} questions are left today. Your selection needs {questions}. Choose fewer papers.',
                        429, max(1, math.ceil(reset-now)), questions_left=remaining)
    return None


def cooldown_error(now, last):
    if last is not None and last + COOLDOWN_SECONDS > now:
        return conflict('CUSTOM_COOLDOWN', 'Wait before starting another Custom Exam.', 429,
                        max(1, math.ceil(last+COOLDOWN_SECONDS-now)))
    return None


def check_cooldown(now):
    last = db.session.scalar(select(CustomExamBrowser.started_at).where(CustomExamBrowser.guest_hash==g.guest_hash))
    return cooldown_error(now, last)


def unfinished(now):
    # Expired attempts are excluded without loading answers or grading on Start.
    row = db.session.execute(select(Attempt.id, Attempt.title).where(
        Attempt.guest_hash==g.guest_hash, Attempt.status=='ACTIVE', Attempt.expires_at>now,
        (Attempt.deadline.is_(None) | (Attempt.deadline>now)),
    ).order_by(Attempt.id.desc()).limit(1)).first()
    if row:
        return conflict('CUSTOM_UNFINISHED', 'You have an unfinished exam or practice session. Finish it or discard it before starting a Custom Exam.',
                        attempt_id=row.id, attempt_title=row.title)
    return None


def state():
    return db.session.get(CustomExamQuota, 1, populate_existing=True)


def admit(questions):
    """Reserve budget in the same transaction as the new attempt."""
    now = time.time()
    day, _ = day_window(now)
    table = CustomExamQuota
    current_day = table.day == day
    used = case((current_day, table.questions_used), else_=0)
    starts = case((current_day, table.starts), else_=0)
    total = db.session.scalar(update(table).where(table.id==1, table.paused.is_(False),
                                                 table.day<=day, used+questions<=DAILY_LIMIT)
                              .values(day=day, questions_used=used+questions, starts=starts+1)
                              .returning(table.questions_used).execution_options(synchronize_session=False))
    if total is None:
        return blocked(state(), now, questions) or conflict(
            'CUSTOM_BUSY', 'Another Custom Exam is being prepared.', 503, 3)

    # Updating the singleton serializes successful admissions across workers.
    browser = db.session.get(CustomExamBrowser, g.guest_hash, populate_existing=True)
    error = cooldown_error(now, browser.started_at if browser else None) or unfinished(now)
    if error:
        db.session.rollback()
        return error
    if total == questions:
        db.session.execute(delete(CustomExamBrowser).where(
            CustomExamBrowser.started_at<=now-COOLDOWN_SECONDS, CustomExamBrowser.guest_hash!=g.guest_hash))
    if browser is None:
        db.session.add(CustomExamBrowser(guest_hash=g.guest_hash, started_at=now))
    else:
        browser.started_at = now
    return None


def overview(paused=None):
    if paused is not None:
        db.session.execute(update(CustomExamQuota).where(CustomExamQuota.id==1).values(paused=paused))
        db.session.commit()
    row = state()
    now = time.time()
    day, reset = day_window(now)
    used, starts = (row.questions_used, row.starts) if row.day == day else (0, 0)
    return dict(enabled=enabled(), paused=row.paused, day=day.isoformat(), resets_at=reset,
                daily_limit=DAILY_LIMIT, questions_used=used, questions_left=DAILY_LIMIT-used,
                starts=starts)
