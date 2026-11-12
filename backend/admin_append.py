"""Bounded, atomic manual additions; existing question/attempt identities stay intact."""
import hashlib,json,math,re,time
from flask import request,abort,jsonify,g
from .models import db,Paper,Question,QuestionOption,QuestionReview,IngestionFile
from .api import require_user,body
from .engine import validate_question


def validate_row(row):
    if not isinstance(row,dict):abort(400,description='Each question must be an object')
    number=row.get('number');kind=row.get('kind','MCQ')
    if not isinstance(number,str) or not number.strip() or len(number.strip())>40:abort(400,description='Enter a question number (maximum 40 characters)')
    data={'number':number.strip(),'kind':kind}
    for name,limit in (('text',20000),('passage',20000),('explanation',20000),('topic',150)):
        value=row.get(name,'')
        if not isinstance(value,str) or len(value)>limit:abort(400,description='Invalid '+name)
        data[name]=value
    options=row.get('options',[])
    if not isinstance(options,list) or len(options)>20:abort(400,description='Maximum 20 options per question')
    clean=[]
    for option in options:
        if not isinstance(option,dict):abort(400,description='Invalid option')
        key=option.get('key');text=option.get('text')
        if not isinstance(key,str) or not key.strip() or len(key)>20 or not isinstance(text,str) or not text.strip() or len(text)>10000:abort(400,description='Each option needs a key and text')
        clean.append({'key':key.strip(),'text':text})
    if len({o['key'] for o in clean})!=len(clean):abort(400,description='Option keys must be unique')
    data['options']=clean
    for name,default in (('marks',None),('negative_marks',0),('tolerance',0)):
        value=row.get(name,default)
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value<0):abort(400,description='Invalid '+name)
        data[name]=value
    data['answers']=row.get('answers')
    data['answer_status']='ANSWER_AVAILABLE' if data['answers'] is not None else 'ANSWER_UNAVAILABLE'
    try:
        validate_question(data)
        if kind=='NAT' and isinstance(data['answers'],dict):
            from .numeric import parse_numeric_key
            if parse_numeric_key(data['answers'].get('raw',''))!=data['answers']:raise ValueError('Invalid NAT range key')
        if kind=='NAT' and isinstance(data['answers'],bool):raise ValueError('NAT answer must be a number')
    except (ValueError,TypeError,KeyError) as exc:abort(400,description=str(exc))
    try:json.dumps(data,allow_nan=False)
    except (ValueError,TypeError):abort(400,description='Answers must contain finite JSON values')
    data['negative_marks']=0
    return data


def register_append_routes(admin):
    @admin.post('/papers/<int:id>/questions/append')
    @require_user(True)
    def append_questions(id):
        if (request.content_length or 0)>256*1024:abort(413,description='Question batch must be under 256 KB')
        b=body();rows=b.get('questions');token=b.get('request_id');publish=b.get('publish',False)
        if not isinstance(rows,list) or not 1<=len(rows)<=20:abort(400,description='Add between 1 and 20 questions per batch')
        if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,64}',token):abort(400,description='Invalid request id')
        if type(publish) is not bool:abort(400,description='Invalid publication choice')
        data=[validate_row(row) for row in rows]
        names=[row['number'].casefold() for row in data]
        if len(set(names))!=len(names):abort(400,description='Question numbers must be unique within the batch')
        digest=hashlib.sha256(json.dumps({'questions':data,'publish':publish},sort_keys=True,allow_nan=False).encode()).hexdigest()
        paper=db.session.execute(db.select(Paper).filter_by(id=id).with_for_update()).scalar_one_or_none()
        if paper is None:abort(404)
        # A paper lock serializes duplicate-number checks and retry deduplication.
        previous=Question.query.filter(Question.paper_id==id,Question.evidence['_append_batch'].as_string()==token).order_by(Question.id).all()
        if previous:
            if len(previous)!=len(data) or any((q.evidence or {}).get('_append_hash')!=digest for q in previous):abort(409,description='This request id was already used for different questions')
            return jsonify(ids=[q.id for q in previous],created=0,replayed=True),200
        if paper.status=='ARCHIVED':abort(409,description='Restore this paper before adding questions')
        if paper.canonical_paper_id:abort(409,description='Append to the original source paper #'+str(paper.canonical_paper_id))
        if IngestionFile.query.filter(IngestionFile.paper_id==id,IngestionFile.status.in_(['QUEUED','FETCH_QUEUED','FETCHING','PROCESSING'])).first():abort(409,description='Wait for this paper to finish processing')
        existing={n.strip().casefold() for n, in db.session.query(Question.number).filter_by(paper_id=id)}
        if existing.intersection(names):abort(409,description='A question number already exists. Edit or restore that question instead.')
        from .admin_content import state,refresh_paper
        created=[]
        for row in data:
            evidence={'_admin_locked':True,'_admin_previous_status':'AVAILABLE','_append_batch':token,'_append_hash':digest,
                      'shared_passage_text':row['passage'] or None,'subquestion_text':row['text'] if row['passage'] else None}
            q=Question(paper_id=id,number=row['number'],kind=row['kind'],text=row['text'],answers=row['answers'],answer_status=row['answer_status'],
                       explanation=row['explanation'],topic=row['topic'],marks=row['marks'],negative_marks=row['negative_marks'],tolerance=row['tolerance'],
                       status='AVAILABLE' if publish else 'HIDDEN',evidence=evidence,confidence=1,updated_at=time.time())
            q.options=[QuestionOption(key=o['key'],text=o['text'],position=n) for n,o in enumerate(row['options'])]
            db.session.add(q);created.append(q)
        db.session.flush()
        for q in created:db.session.add(QuestionReview(question_id=q.id,user_id=g.user.id,action='APPEND',before={},after=state(q)))
        # A draft-only addition must not change an existing paper's availability.
        if publish:refresh_paper(created[0])
        db.session.commit()
        return jsonify(ids=[q.id for q in created],created=len(created),replayed=False),201
