"""Shared content cache. Student/session state is never cached here."""
import json, time, uuid, threading, sys
from collections import OrderedDict
from flask import current_app, has_app_context
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from .performance import count

CONTENT_TABLES = {'course', 'term', 'exam_type', 'paper', 'question', 'question_option',
                  'question_image', 'ingestion_file', 'ai_solution'}

CACHE_SCOPES = ('catalog', 'snapshots', 'solutions', 'other', 'admin', 'admin-solutions')

def _scope(key):
    if key.startswith('admin-campaign:'):return 'admin'
    if key.startswith('admin-solution-summary:'):return 'admin-solutions'
    if key.startswith('paper:'):return 'snapshots'
    if key.startswith('paper-published-solutions:'):return 'solutions'
    if key == 'site-feedback':return 'other'
    return 'catalog'

def _changed_scopes(table):
    # Import progress does not change questions. Source-entry bookkeeping is
    # not read by public caches; changes to actual Paper rows still invalidate.
    if table == 'ingestion_file':return {'catalog', 'admin'}
    if table == 'ai_solution':return {'catalog', 'solutions', 'admin-solutions'}
    return set(CACHE_SCOPES) if table in CONTENT_TABLES else set()

# A small per-process fallback matters on Render even before Redis is provisioned:
# the same paper should not be rebuilt from PostgreSQL for every student. Redis
# remains the preferred shared cache across processes/services.
_local_lock = threading.RLock()
_local_cache = OrderedDict()
_local_inflight = {}
_local_generation = 0
_local_sizes = {}
_local_bytes = 0


def _byte_limit():
    return max(0,int(current_app.config.get('LOCAL_CONTENT_CACHE_BYTES',32*1024*1024)))


def _retained_size(value, limit):
    """Estimate retained Python objects without allocating a JSON copy."""
    seen=set();pending=[value];size=0
    while pending:
        item=pending.pop();identity=id(item)
        if identity in seen:continue
        seen.add(identity);size+=sys.getsizeof(item)
        if size>limit:return size
        if isinstance(item,dict):pending.extend(item.keys());pending.extend(item.values())
        elif isinstance(item,(list,tuple,set,frozenset)):pending.extend(item)
    return size


def _local_drop(key):
    global _local_bytes
    _local_cache.pop(key,None)
    _local_bytes-=_local_sizes.pop(key,0)


def local_cache_usage():
    with _local_lock:
        return {'entries':len(_local_cache),'estimated_bytes':_local_bytes}


def _local_limit():
    return max(8, int(current_app.config.get('LOCAL_CONTENT_CACHE_MAX', 128)))


def _ttl(key):
    ttl=_local_ttl()
    return min(ttl,15) if _scope(key) in ('admin','admin-solutions') else ttl

def _local_ttl():
    return max(1, int(current_app.config.get('CONTENT_CACHE_TTL', 60)))


def _local_get(key):
    now=time.monotonic()
    with _local_lock:
        row=_local_cache.get(key)
        if row is None:return None
        expires,value=row
        if expires<=now:
            _local_drop(key);return None
        _local_cache.move_to_end(key)
        return value


def _local_put(key,value):
    global _local_bytes
    budget=_byte_limit();size=_retained_size(value,budget)
    with _local_lock:
        # TTL alone does not free objects until a key is looked up again.
        now=time.monotonic()
        for old,(expires,_) in list(_local_cache.items()):
            if expires<=now:_local_drop(old)
        _local_drop(key)
        if not budget or size>budget:return
        _local_cache[key]=(time.monotonic()+_ttl(key),value)
        _local_sizes[key]=size;_local_bytes+=size
        _local_cache.move_to_end(key)
        while len(_local_cache)>_local_limit() or _local_bytes>budget:
            _local_drop(next(iter(_local_cache)))


def _local_clear(scopes=None):
    global _local_generation,_local_bytes
    with _local_lock:
        _local_generation += 1
        if scopes is None:
            _local_cache.clear()
            _local_sizes.clear();_local_bytes=0
        else:
            for key in list(_local_cache):
                if _scope(key) in scopes:_local_drop(key)


def _local_cached(key,loader):
    value=_local_get(key)
    if value is not None:
        count('cache_hit');return value
    count('cache_miss')
    owner=False
    with _local_lock:
        generation=_local_generation
        event=_local_inflight.get(key)
        if event is None:
            event=threading.Event();_local_inflight[key]=event;owner=True
    if not owner:
        # Let one thread warm a paper; a bounded wait avoids a thundering herd
        # during simultaneous exam starts without ever hanging a request.
        if event.wait(timeout=5.0):
            value=_local_get(key)
            if value is not None:
                count('cache_hit');return value
        return loader()
    try:
        value=loader()
        with _local_lock:
            if generation==_local_generation:_local_put(key,value)
        return value
    finally:
        with _local_lock:
            _local_inflight.pop(key,None);event.set()


def client():
    app = current_app
    if not app.config.get('CONTENT_CACHE_URL'):
        return None
    if 'content_redis' not in app.extensions:
        from redis import Redis
        app.extensions['content_redis'] = Redis.from_url(app.config['CONTENT_CACHE_URL'],
            socket_connect_timeout=.3, socket_timeout=.3, decode_responses=True,
            max_connections=16)
    return app.extensions['content_redis']


def prefix():
    return current_app.config.get('CACHE_NAMESPACE', 'pyq:content:v1')


def invalidate(scopes=None):
    _local_clear(scopes)
    try:
        r = client()
        if r is not None:
            for scope in (CACHE_SCOPES if scopes is None else scopes):
                r.set(prefix()+':epoch:'+scope, uuid.uuid4().hex)
    except Exception:
        current_app.logger.warning('content_cache_invalidation_failed; entries expire within configured TTL')

invalidate_content_cache = invalidate


def forget(key):
    """Drop one cached entry without clearing the whole content cache.

    Used for data outside CONTENT_TABLES (for example site feedback), so a
    single public post never forces every paper/course entry to be rebuilt.
    """
    global _local_generation
    with _local_lock:
        _local_drop(key)
        _local_generation+=1
    try:
        r = client()
        if r is not None:
            r.set(prefix()+':forgot:'+key,uuid.uuid4().hex,ex=max(60,_ttl(key)))
            epoch = r.get(prefix()+':epoch:'+_scope(key))
            if epoch:
                r.delete(prefix()+':'+str(epoch)+':'+key)
    except Exception:
        current_app.logger.warning('content_cache_forget_failed; entry expires within configured TTL')

def cached(key, loader):
    with _local_lock:generation=_local_generation
    lock = None
    acquired = False
    try:
        r = client()
    except Exception:
        count('cache_error');return _local_cached(key,loader)
    if r is None:return _local_cached(key,loader)
    try:
        epoch_key = prefix()+':epoch:'+_scope(key)
        r.set(epoch_key, uuid.uuid4().hex, nx=True)
        epoch = r.get(epoch_key)
        full = prefix()+':'+str(epoch)+':'+key
        forgot_key=prefix()+':forgot:'+key
        forgot=r.get(forgot_key) or ''
        raw = r.get(full)
        if raw is not None:
            count('cache_hit');return json.loads(raw)
        count('cache_miss')
        lock = r.lock(full+':lock', timeout=15, blocking_timeout=5.0)
        acquired = lock.acquire()
        raw = r.get(full)
        if raw is not None:
            if acquired:lock.release();acquired=False
            return json.loads(raw)
    except Exception:
        if acquired:
            try:lock.release()
            except Exception:pass
        count('cache_error');return _local_cached(key,loader)
    try:
        value = loader()  # Application exceptions propagate; no duplicate execution.
        stored=False
        if acquired:
            try:
                stored=bool(r.eval("if redis.call('get',KEYS[1])==ARGV[1] and (redis.call('get',KEYS[2]) or '')==ARGV[2] then return redis.call('set',KEYS[3],ARGV[3],'EX',ARGV[4]) end return 0",3,epoch_key,forgot_key,full,epoch,forgot,json.dumps(value),_ttl(key)))
            except Exception:count('cache_error')
        with _local_lock:
            if stored and generation==_local_generation:_local_put(key,value)
        return value
    finally:
        if acquired:
            try:lock.release()
            except Exception:pass


PAPER_LEVEL_TABLES = {'question', 'question_option', 'question_image', 'ai_solution'}


def paper_keys(paper_id):
    return ('paper:'+str(paper_id)+':snapshots:msq-proportional-v1',
            'paper-published-solutions:'+str(paper_id))


def _question_paper_ids(session, question_id, paper_map):
    from .models import Question
    if question_id is None:return None
    if question_id in paper_map:
        return {paper_map[question_id]} if paper_map[question_id] is not None else set()
    with session.no_autoflush:
        pid = session.query(Question.paper_id).filter(Question.id == question_id).scalar()
    return {pid} if pid is not None else set()


def _changed_paper_ids(session, obj, table, paper_map):
    """Paper ids a question-level row belongs to (old and new), or None when
    they cannot be known safely (then the whole scope is invalidated)."""
    state = inspect(obj)
    if table == 'question':
        hist = state.attrs.paper_id.history
        ids = {v for v in (*hist.added, *hist.unchanged, *hist.deleted) if v is not None}
        if state.persistent and ((hist.has_changes() and not hist.deleted) or (not ids and 'paper_id' in state.unloaded)):
            with session.no_autoflush:
                pid = session.query(type(obj).paper_id).filter(type(obj).id == state.identity[0]).scalar()
            ids |= {pid} if pid is not None else set()
        return ids or None
    question = state.dict.get('question')
    related_ids={question.paper_id} if question is not None and getattr(question,'paper_id',None) is not None else set()
    hist = state.attrs.question_id.history
    qids = {v for v in (*hist.added, *hist.unchanged, *hist.deleted) if v is not None}
    if state.persistent and ((hist.has_changes() and not hist.deleted) or (not qids and 'question_id' in state.unloaded)):
        with session.no_autoflush:
            qid = session.query(type(obj).question_id).filter(type(obj).id == state.identity[0]).scalar()
        qids |= {qid} if qid is not None else set()
    if not qids:
        # A new child attached through its parent's collection: the parent
        # question is in this flush and supplies the paper id.
        return related_ids if related_ids or obj in session.new else None
    ids = related_ids
    for qid in qids:
        found = _question_paper_ids(session, qid, paper_map)
        if found is None:return None
        ids |= found
    return ids


@event.listens_for(Session, 'before_flush')
def changed(session, context, instances):
    scopes=set();papers=set()
    objects=session.new.union(session.dirty).union(session.deleted)
    # Resolve all known child foreign keys in one slim SELECT per flush, not
    # one database round trip per published solution/option/image.
    qids=set()
    for obj in objects:
        if getattr(obj,'__tablename__','') in PAPER_LEVEL_TABLES-{'question'}:
            hist=inspect(obj).attrs.question_id.history
            qids.update(v for v in (*hist.added,*hist.unchanged,*hist.deleted) if v is not None)
    from .models import Question
    with session.no_autoflush:
        paper_map=dict(session.query(Question.id,Question.paper_id).filter(Question.id.in_(qids)).all()) if qids else {}
    for obj in objects:
        table=getattr(obj, '__tablename__', '')
        if table in PAPER_LEVEL_TABLES:
            ids=_changed_paper_ids(session,obj,table,paper_map)
            if ids is not None:
                papers |= ids
                scopes.update({'catalog','admin','admin-solutions'})
                continue
        if table=='ingestion_file' and obj in session.dirty:
            # Only download availability depends on this row. Status, retry
            # counters and extraction events are admin bookkeeping.
            state=inspect(obj)
            if state.attrs.status.history.has_changes():scopes.add('admin')
            if not any(state.attrs[name].history.has_changes() for name in ('path','paper_id')):continue
        scopes.update(_changed_scopes(table))
    if scopes:session.info.setdefault('content_changed',set()).update(scopes)
    if papers:session.info.setdefault('content_papers',set()).update(papers)


@event.listens_for(Session, 'do_orm_execute')
def bulk_changed(state):
    if state.is_update or state.is_delete or state.is_insert:
        table = getattr(state.statement, 'table', None)
        scopes=_changed_scopes(getattr(table, 'name', None))
        if scopes:state.session.info.setdefault('content_changed',set()).update(scopes)


@event.listens_for(Session, 'after_commit')
def committed(session):
    if session.in_nested_transaction():
        return
    scopes=session.info.pop('content_changed', None)
    papers=session.info.pop('content_papers',None)
    if not has_app_context():return
    if scopes:invalidate(scopes)
    for pid in papers or ():
        for key in paper_keys(pid):forget(key)


@event.listens_for(Session, 'after_soft_rollback')
def rolled_back(session, previous):
    if previous.parent is None:
        session.info.pop('content_changed', None)
        session.info.pop('content_papers', None)
