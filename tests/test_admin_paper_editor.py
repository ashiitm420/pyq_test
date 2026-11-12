import pytest
from backend.models import db,Question,QuestionReview,AttemptAnswer
from conftest import login
from test_engine import seed

def url(pid):return f'/api/admin/papers/{pid}/questions/edit'
def read(client,p):return client.get(url(p.id)).json['items']
def item(row,**changes):return dict(id=row['question']['id'],updated_at=row['updated_at'],**changes)

def test_paper_batch_is_atomic_versioned_and_preserves_attempts(app,client):
    p=seed();guest=login(client)
    attempt=client.post('/api/attempts',headers=guest,json={'paper_id':p.id,'mode':'exam'}).json
    h=login(client,True);rows=read(client,p)
    a,b=rows[:2];original=a['question']['text']
    r=client.patch(url(p.id),headers=h,json={'questions':[item(a,text='Changed together',marks=5),item(b,explanation='New explanation')]})
    assert r.status_code==200,r.json
    assert len(r.json['saved'])==2 and QuestionReview.query.count()==2
    assert db.session.get(Question,a['question']['id']).marks==5
    assert AttemptAnswer.query.filter_by(attempt_id=attempt['id'],question_id=a['question']['id']).one().snapshot['text']==original
    r=client.patch(url(p.id),headers=h,json={'questions':[item(a,text='stale')]})
    assert r.status_code==409
    rows=read(client,p);a,b=rows[:2]
    r=client.patch(url(p.id),headers=h,json={'questions':[item(a,text='Should roll back'),item(b,marks=-5)]})
    assert r.status_code==400 and db.session.get(Question,a['question']['id']).text=='Changed together'


def test_editor_read_is_slim_and_hidden_stays_hidden(app,client):
    p=seed();h=login(client,True);q=Question.query.filter_by(paper_id=p.id).first()
    q.status='HIDDEN';q.evidence={'debug_blob':'x'*5000,'_active_image_ids':[]};db.session.commit()
    r=client.get(url(p.id));assert r.status_code==200
    assert 'debug_blob' not in r.text
    row=next(x for x in r.json['items'] if x['question']['id']==q.id)
    assert client.patch(url(p.id),headers=h,json={'questions':[item(row,text='Hidden corrected')]}).status_code==200
    assert q.status=='HIDDEN' and q.evidence['debug_blob']=='x'*5000


def test_editor_authorization_csrf_limits_and_membership(app,client):
    p=seed();assert client.get(url(p.id)).status_code==401
    login(client);assert client.get(url(p.id)).status_code==401
    h=login(client,True);row=read(client,p)[0];change=item(row,text='new')
    assert client.patch(url(p.id),json={'questions':[change]}).status_code==403
    assert client.patch(url(p.id),headers=h,json={'questions':[change,change]}).status_code==400
    assert client.patch(url(p.id),headers=h,json={'questions':[dict(change,id=99999)]}).status_code==404
    p.status='ARCHIVED';db.session.commit();assert client.get(url(p.id)).status_code==409


def test_incomplete_marks_percentage_uses_only_gradable_subset():
    from types import SimpleNamespace as N
    from backend.engine import aggregate
    def row(marks,outcome,awarded,known=True):return N(snapshot=dict(marks=marks,kind='MCQ',answer_status='ANSWER_AVAILABLE' if known else 'ANSWER_UNAVAILABLE',negative_marks=0),outcome=outcome,awarded=awarded)
    a=N(items=[row(4,'CORRECT',4),row(4,'SKIPPED',0),row(None,'UNGRADED',None),row(2,'UNGRADED',None,False)],started_at=0,submitted_at=60)
    r=aggregate(a)
    assert r['score']==4 and r['total_marks']==8 and r['percentage']==50
    assert r['partial_score'] and r['excluded_from_score']==2 and r['pending_manual']
    a.items=[row(None,'UNGRADED',None)];assert aggregate(a)['percentage'] is None


def test_processing_blocks_batch_and_reader_avoids_debug_column(app,client):
    from sqlalchemy import event
    from backend.models import IngestionFile,IngestionBatch,User
    p=seed();h=login(client,True);statements=[]
    def capture(conn,cursor,statement,parameters,context,many):statements.append(statement)
    event.listen(db.engine,'before_cursor_execute',capture)
    try:rows=read(client,p)
    finally:event.remove(db.engine,'before_cursor_execute',capture)
    assert not any('question.evidence AS question_evidence' in s for s in statements)
    batch=IngestionBatch(user_id=User.query.filter_by(role='ADMIN').first().id);db.session.add(batch);db.session.flush()
    job=IngestionFile(batch_id=batch.id,paper_id=p.id,status='PROCESSING',filename='x.pdf',path='x.pdf')
    db.session.add(job);db.session.commit()
    assert client.patch(url(p.id),headers=h,json={'questions':[item(rows[0],text='blocked')]}).status_code==409
