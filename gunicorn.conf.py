"""Conservative defaults; select final counts from staging load measurements."""
import os
bind = '0.0.0.0:'+os.getenv('PORT','5000')
worker_class = 'gthread'
workers = int(os.getenv('WEB_CONCURRENCY','1'))
threads = int(os.getenv('GUNICORN_THREADS','8'))
timeout = int(os.getenv('GUNICORN_TIMEOUT','60'))
graceful_timeout = 30
keepalive = 5
# Slow native-library growth needs a safety net in addition to bounded caches.
# This is not an OOM fix by itself; warmup still runs for the replacement worker.
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS','10000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER','1000'))
accesslog = '-'
errorlog = '-'
# No query strings, signed URLs, headers or request bodies in access logs.
access_log_format = '%(m)s %(s)s %(D)s'


def post_worker_init(worker):
    # Shift first-use DB/signing/catalog setup out of the first learner request.
    # A temporary warmup failure must not prevent the service from starting.
    try:
        from backend.warmup import warm_public_content
        elapsed=warm_public_content(worker.wsgi)
        worker.log.info('public_content_warmup_ms=%d',elapsed)
    except Exception as exc:
        worker.log.warning('public_content_warmup_failed type=%s',type(exc).__name__)
