"""Request timings without SQL text, parameters, user IDs or credential URLs."""
import time,threading,logging
from pathlib import Path
from contextlib import contextmanager
from flask import g, has_request_context, request
from sqlalchemy import event


@contextmanager
def span(name):
    start = time.perf_counter()
    try:
        yield
    finally:
        if has_request_context() and hasattr(g, 'perf'):
            g.perf[name] = g.perf.get(name, 0) + (time.perf_counter() - start) * 1000


def count(name):
    if has_request_context() and hasattr(g, 'perf'):
        g.perf[name] = g.perf.get(name, 0) + 1


def install(app, db):
    if app.config.get('MEMORY_LOG_INTERVAL_SECONDS',60)>0:
        app.logger.setLevel(min(app.logger.getEffectiveLevel(),logging.INFO))
    memory_lock=threading.Lock();last_memory_log=[0.0]
    processing=threading.BoundedSemaphore(1)
    app.extensions['processing_slots']=processing
    # Acquire before an endpoint parses uploads or claims a job. Competing admin
    # requests must not multiply PDF/workbook allocations in one web worker.
    heavy_endpoints={'admin.run_catalog_batch_next','admin.process_now','admin.upload',
                     'admin.upload_pyq','admin.replace_pdf','admin.upload_question_image',
                     'admin.preview_catalog','admin.apply_catalog','admin.import_catalog',
                     'admin.refresh_master_catalog'}
    @app.before_request
    def begin():
        g.perf = {'start': time.perf_counter(), 'sql': 0, 'queries': 0}
        if request.endpoint in heavy_endpoints:
            if not processing.acquire(blocking=False):
                from flask import jsonify
                return jsonify(error='Another upload or processing request is running. Retry when it finishes.',code='PROCESSING_BUSY'),409,{'Retry-After':'5'}
            g.processing_slot=True

    @app.teardown_request
    def release_processing(error):
        if g.pop('processing_slot',False):processing.release()

    def before(conn, cursor, statement, parameters, context, many):
        context._pyq_started = time.perf_counter()

    def after(conn, cursor, statement, parameters, context, many):
        if has_request_context() and hasattr(g, 'perf'):
            g.perf['sql'] += (time.perf_counter() - context._pyq_started) * 1000
            g.perf['queries'] += 1

    def connect(dialect, record, args, params):
        with span('db_connect'):
            return dialect.connect(*args,**params)

    with app.app_context():
        event.listen(db.engine,'do_connect',connect,retval=True)
        event.listen(db.engine, 'before_cursor_execute', before)
        event.listen(db.engine, 'after_cursor_execute', after)

    @app.after_request
    def finish(response):
        metrics = getattr(g, 'perf', None)
        if metrics is None:
            return response
        elapsed = (time.perf_counter() - metrics['start']) * 1000
        values = [f'app;dur={elapsed:.2f}', f'sql;dur={metrics["sql"]:.2f}',
                  f'queries;desc="{metrics["queries"]}"']
        for name in ('ensure_local', 'r2_download', 'disk_write', 'send_asset', 'attempt_insert', 'answer_insert', 'commit', 'bootstrap', 'db_connect', 'image_metadata'):
            if name in metrics:
                values.append(f'{name};dur={metrics[name]:.2f}')
        for name in ('asset_hit', 'asset_miss', 'cache_hit', 'cache_miss', 'cache_error'):
            if name in metrics:
                values.append(f'{name};desc="{metrics[name]}"')
        response.headers['Server-Timing'] = ', '.join(values)
        if elapsed >= app.config.get('SLOW_REQUEST_MS', 750):
            # Route template only: no actual path, query strings, body or SQL.
            route = str(request.url_rule) if request.url_rule else 'unmatched'
            app.logger.warning('slow_request route=%s method=%s status=%s app_ms=%.1f sql_ms=%.1f queries=%d',
                               route, request.method, response.status_code, elapsed, metrics['sql'], metrics['queries'])
        interval=app.config.get('MEMORY_LOG_INTERVAL_SECONDS',60)
        now=time.monotonic()
        if interval>0 and now-last_memory_log[0]>=interval and memory_lock.acquire(blocking=False):
            try:
                if now-last_memory_log[0]>=interval:
                    last_memory_log[0]=now
                    from .content_cache import local_cache_usage
                    usage=local_cache_usage();rss=current_rss_bytes()
                    app.logger.info('memory_sample rss_bytes=%d cache_estimated_bytes=%d cache_entries=%d threads=%d route=%s',
                                    rss,usage['estimated_bytes'],usage['entries'],threading.active_count(),str(request.url_rule) if request.url_rule else 'unmatched')
            finally:memory_lock.release()
        return response


def current_rss_bytes():
    """Current Linux RSS, not the never-decreasing ru_maxrss high-water mark."""
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):return int(line.split()[1])*1024
    except (OSError,ValueError):pass
    return 0
