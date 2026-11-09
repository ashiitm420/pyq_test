"""Bounded admin experiment; no public rollout, new tables or analytics writes."""
import json,time,threading
from flask import abort,g,current_app,jsonify
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from .models import db,Paper,Question,Attempt
from .engine import RESULT_TTL_SECONDS

MAX_PAPERS=4
MAX_QUESTIONS=125
MAX_SNAPSHOT_BYTES=1024*1024
_start_slot=threading.BoundedSemaphore(1)

def metadata(a):
    context=a.analytics_context or {}
    return context.get('custom_exam')

def check_access(a):
    meta=metadata(a)
    if meta and (getattr(g.user,'role',None)!='ADMIN' or g.user.id!=meta['admin_id']):
        abort(403,description='This experimental custom exam is available only to its administrator.')

def start(b):
    if getattr(g.user,'role',None)!='ADMIN':abort(403,description='Custom exams are admin-only during testing.')
    if not _start_slot.acquire(blocking=False):
        return jsonify(error='Another custom exam is starting. Retry shortly.',code='START_BUSY'),503,{'Retry-After':'3'}
    try:return _start(b)
    finally:_start_slot.release()

def _start(b):
    ids=b.get('paper_ids');duration=b.get('duration_seconds')
    if not isinstance(ids,list) or not 1<=len(ids)<=MAX_PAPERS or any(type(x)!=int or x<1 for x in ids) or len(set(ids))!=len(ids):
        abort(400,description='Choose 1–4 unique papers.')
    if type(duration)!=int or not 60<=duration<=28800:abort(400,description='Choose 1–480 whole minutes.')
    mode=b.get('mode','exam')
    if mode not in ('exam','practice') or b.get('collection'):abort(400,description='Choose exam or practice.')
    papers={p.id:p for p in Paper.query.options(joinedload(Paper.course),joinedload(Paper.term),joinedload(Paper.exam_type)).filter(Paper.id.in_(ids),Paper.status!='ARCHIVED')}
    if len(papers)!=len(ids):abort(404,description='A selected paper is unavailable.')
    effective=[papers[i].canonical_paper_id or i for i in ids]
    if len(set(effective))!=len(effective):abort(400,description='Two selections refer to the same source paper.')
    sources={p.id:p for p in Paper.query.filter(Paper.id.in_(effective))}
    if len(sources)!=len(effective) or any(p.status=='ARCHIVED' for p in sources.values()):abort(409,description='A source paper is archived.')
    counts=dict(db.session.query(Question.paper_id,func.count(Question.id)).filter(Question.paper_id.in_(effective),Question.status=='AVAILABLE').group_by(Question.paper_id))
    if any(not counts.get(i) for i in effective):abort(409,description='Every selected paper must have available questions.')
    if sum(counts.values())>MAX_QUESTIONS:abort(400,description='Custom exams are limited to 125 total questions during testing. No paper will be truncated.')
    from .paper_content import snapshots
    all_snapshots=[];sections=[];size=0
    for pid,eid in zip(ids,effective):
        p=papers[pid];rows=snapshots(eid)
        if len(rows)!=counts[eid]:abort(409,description='Paper content changed. Refresh the selection and retry.')
        size+=sum(len(json.dumps(s,ensure_ascii=False,separators=(',',':')).encode()) for s in rows)
        if size>MAX_SNAPSHOT_BYTES:abort(400,description='Selected paper content exceeds the 1 MiB test limit. Choose fewer papers.')
        all_snapshots.extend(rows)
        sections.append(dict(id=pid,source_paper_id=eid,title=f'{p.course.name} · {p.exam_type.name} · {p.term.name} · {p.name}',questions=len(rows)))
    # Cached snapshots are never modified. One bulk insert, one timer, no new queue.
    deadline=time.time()+duration if mode=='exam' else None
    a=Attempt(guest_hash=g.guest_hash,user_id=None,paper_id=None,mode=mode,title=f'Custom exam · {len(sections)} papers · admin test',deadline=deadline,expires_at=deadline+RESULT_TTL_SECONDS if deadline else time.time()+86400,records_progress=False,analytics_context={'custom_exam':{'admin_id':g.user.id,'duration_seconds':duration,'remaining_seconds':duration,'direct_images':all((sources[i].source_metadata or {}).get('question_assets_verified_r2') for i in effective),'papers':sections}})
    from .exam_api import finish_new_attempt
    return finish_new_attempt(a,all_snapshots)

def switch_mode(a,b):
    from .engine import ACTIVE_TTL_SECONDS,grade
    from .exam_api import attempt_status_json
    mode=b.get('mode')
    if a.status!='ACTIVE':abort(409,description='This attempt has ended')
    if mode not in ('practice','exam') or mode==a.mode:abort(400,description='Select the other mode')
    now=time.time();context=dict(a.analytics_context);meta=dict(context['custom_exam'])
    if mode=='practice':
        meta['remaining_seconds']=max(0,(a.deadline or now)-now)
        a.deadline=None;a.expires_at=now+ACTIVE_TTL_SECONDS
    else:
        remaining=meta.get('remaining_seconds',meta.get('duration_seconds',5400))
        if remaining<=0:abort(409,description='The exam time has expired')
        a.deadline=now+remaining;a.expires_at=a.deadline+RESULT_TTL_SECONDS
    context['custom_exam']=meta;context['assisted']=True;a.analytics_context=context;a.mode=mode
    feedback=[{'question_id':i.question_id,'feedback':{**grade(i.snapshot,i.answer),'answers':i.snapshot['answers'],'explanation':i.snapshot['explanation'],'answer_status':i.snapshot['answer_status']}} for i in a.items if i.answer is not None] if mode=='practice' else []
    db.session.commit()
    return jsonify({**attempt_status_json(a),'mode':mode,'title':a.title,'feedback':feedback})
