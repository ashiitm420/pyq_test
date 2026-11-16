"""Idempotent, audited application of a bundled source-verified key manifest.

Runs once before Gunicorn, never from a learner request. No PDF extraction occurs
on Render. Existing attempts retain their immutable question snapshots.
"""
import copy,hashlib,json,time
from pathlib import Path
from flask import g
from sqlalchemy.orm import selectinload
from .models import db,Question,Paper,User,ImportRun,IngestionFile

REPAIR_ID='source-verified-answer-keys-20261116-v1'
RECEIPT=hashlib.sha256(REPAIR_ID.encode()).hexdigest()
MANIFEST=Path(__file__).with_name('data')/'verified_answer_keys_20261116.json'


def apply_verified_keys(manifest_path=None):
    try:return _apply_verified_keys(manifest_path)
    except Exception:
        db.session.rollback()
        raise


def _apply_verified_keys(manifest_path=None):
    # One small receipt read per startup; no manifest/PDF load on subsequent boots.
    if db.session.query(ImportRun.id).filter(ImportRun.workbook_hash==RECEIPT).first():
        return {'already_applied':True,'updated':0}
    data=json.loads(Path(manifest_path or MANIFEST).read_text())
    if data.get('repair_id')!=REPAIR_ID:raise ValueError('Unexpected repair manifest')
    entries=data['questions'];ids=[r['id'] for r in entries]
    if len(ids)!=len(set(ids)) or len(ids)>215:raise ValueError('Invalid repair size or duplicate question')
    from .admin_content import state,audit
    from .engine import question_snapshot,validate_question
    paper_ids=sorted({r['paper_id'] for r in entries})
    papers=dict(db.session.query(Paper.id,Paper.status).filter(Paper.id.in_(paper_ids)).order_by(Paper.id).with_for_update().all())
    busy={r[0] for r in db.session.query(IngestionFile.paper_id).filter(IngestionFile.paper_id.in_(paper_ids),IngestionFile.status.in_(['QUEUED','FETCH_QUEUED','FETCHING','PROCESSING'])).distinct()}
    rows={q.id:q for q in db.session.query(Question).options(selectinload(Question.options),selectinload(Question.images)).filter(Question.id.in_(ids)).order_by(Question.id).with_for_update().all()}
    updated=[];skipped=[]
    admin=None
    for record in entries:
        q=rows.get(record['id'])
        matches=q is not None and q.paper_id==record['paper_id'] and q.ingestion_file_id==record['ingestion_file_id'] and q.number==record['number'] and q.kind==record['kind'] and q.kind in ('NAT','MCQ','MSQ','TRUE_FALSE','SHORT_TEXT') and q.status=='AVAILABLE' and papers.get(q.paper_id)!='ARCHIVED' and q.paper_id not in busy
        if matches:
            matches=q.updated_at==record['expected_updated_at'] and q.marks==record['marks'] and q.answers==record['old_answers'] and q.answer_status==record['old_answer_status'] and not (q.evidence or {}).get('_admin_locked') and (q.evidence or {}).get('source_question_id')==record['source_question_id']
        if not matches:
            skipped.append(record['id']);continue
        if admin is None:
            admin=User.query.filter_by(role='ADMIN',active=True).order_by(User.id).first()
            if admin is None:raise ValueError('An active administrator is required for correction history')
            g.user=admin
        if record['kind']=='NAT':
            from .numeric import parse_numeric_answer_block
            if parse_numeric_answer_block(record['raw_key'])!=record['answers']:
                raise ValueError('Manifest numeric key differs from verified source text')
        before=state(q)
        q.answers=copy.deepcopy(record['answers']);q.answer_status='ANSWER_AVAILABLE'
        q.evidence={**(q.evidence or {}),'_admin_locked':True,'_source_key_repair':{'id':REPAIR_ID,'source_question_id':record['source_question_id'],'source_pdf_sha256':record['source_pdf_sha256'],'raw_key':record['raw_key'],'verification':record['verification']}}
        q.warnings=[w for w in (q.warnings or []) if w!='ANSWER_UNAVAILABLE' and not (isinstance(w,str) and w.startswith('UNPARSED_NUMERIC_KEY:'))]
        validate_question(question_snapshot(q))
        audit(q,before,'SOURCE_KEY_REPAIR',refresh=False)
        updated.append(q.id)
    summary={'mode':REPAIR_ID,'updated':len(updated),'question_ids':updated,'skipped_ids':skipped,'created_at':time.time()}
    db.session.add(ImportRun(workbook_hash=RECEIPT,report=summary))
    # Existing ORM hooks forget only affected paper/solution keys after commit.
    db.session.commit()
    return {'already_applied':False,'updated':len(updated),'skipped':len(skipped)}
