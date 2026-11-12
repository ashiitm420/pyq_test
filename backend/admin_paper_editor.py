"""Bounded paper editor. Atomic changed-only writes, current-version checks."""
from flask import request,jsonify,abort
from sqlalchemy.orm import selectinload,load_only
from .models import db,Paper,Question,IngestionFile
from .api import require_user,body
from .engine import question_snapshot,question_order

LIMIT=125

def editable_paper(pid,lock=False):
    query=Paper.query.filter_by(id=pid)
    p=(query.with_for_update() if lock else query).first_or_404()
    if p.status=='ARCHIVED' or p.canonical_paper_id:abort(409,description='Open an active original paper to edit its questions.')
    if IngestionFile.query.filter(IngestionFile.paper_id==pid,IngestionFile.status.in_(['QUEUED','FETCH_QUEUED','FETCHING','PROCESSING'])).first():
        abort(409,description='Wait for paper processing to finish before editing.')
    return p


def register_paper_editor(admin):
    @admin.get('/papers/<int:pid>/questions/edit')
    @require_user(True)
    def paper_question_editor(pid):
        editable_paper(pid)
        from .paper_content import slim_session,slim_question_query,apply_slim_evidence
        # Full extraction diagnostics stay in DB. Editor keeps only snapshot fields.
        with slim_session() as session:
            rows=slim_question_query(session).options(load_only(Question.updated_at,Question.status),selectinload(Question.options),selectinload(Question.images)).filter(Question.paper_id==pid,Question.status.notin_(['SUPERSEDED','INSTRUCTION'])).order_by(Question.id).limit(LIMIT+1).all()
            if len(rows)>LIMIT:abort(413,description='Use the single-question editor for papers larger than 125 questions.')
            result=[]
            for q,*e in rows:
                apply_slim_evidence(q,e)
                result.append(dict(question=question_snapshot(q),updated_at=q.updated_at,status=q.status))
        result.sort(key=lambda r:question_order(r['question']['number']))
        return jsonify(items=result)

    @admin.patch('/papers/<int:pid>/questions/edit')
    @require_user(True)
    def save_paper_questions(pid):
        if request.content_length and request.content_length>2*1024*1024:abort(413,description='Save fewer changed questions in this batch.')
        updates=body().get('questions')
        if not isinstance(updates,list) or not 1<=len(updates)<=LIMIT:abort(400,description='Choose 1–125 changed questions.')
        if any(not isinstance(u,dict) or type(u.get('id')) is not int for u in updates):abort(400,description='Invalid question IDs.')
        ids=[u['id'] for u in updates]
        if len(set(ids))!=len(ids):abort(400,description='Duplicate question IDs.')
        editable_paper(pid,lock=True)
        rows=Question.query.options(selectinload(Question.options),selectinload(Question.images)).filter(Question.paper_id==pid,Question.id.in_(ids),Question.status.notin_(['SUPERSEDED','INSTRUCTION'])).with_for_update().populate_existing().all()
        if len(rows)!=len(ids):abort(404,description='Question no longer belongs to this paper.')
        from .admin_content import state,validated_edit,apply,audit,refresh_paper
        by_id={q.id:q for q in rows};prepared=[]
        for u in updates:
            q=by_id[u['id']]
            if u.get('updated_at')!=q.updated_at:abort(409,description='Question '+q.number+' changed. Reopen the editor before saving; no changes were saved.')
            prepared.append((q,state(q),validated_edit(q,u)))
        # Validate every row before the first mutation; one commit for all changes.
        for q,before,data in prepared:
            apply(q,data);audit(q,before,'EDIT',refresh=False)
        db.session.flush();refresh_paper(rows[0])
        saved=[dict(id=q.id,updated_at=q.updated_at) for q in rows]
        db.session.commit()
        return jsonify(saved=saved)
