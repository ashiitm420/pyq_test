import uuid,pytest
from backend.models import db,Question,Paper,IngestionFile,IngestionBatch,QuestionReview,User,Attempt
from conftest import login
from test_engine import seed


def row(number='6'):
    return dict(number=number,kind='MCQ',text='Missing question '+number,options=[{'key':'A','text':'Yes'},{'key':'B','text':'No'}],answers=['B'],marks=2,negative_marks=0)

def payload(*rows,publish=False):return {'request_id':uuid.uuid4().hex,'questions':list(rows),'publish':publish}

def test_append_is_admin_only_and_requires_csrf(app,client):
    p=seed();url=f'/api/admin/papers/{p.id}/questions/append'
    assert client.post(url,json=payload(row()),headers=login(client)).status_code==401
    login(client,True)
    assert client.post(url,json=payload(row())).status_code==403
    assert Question.query.count()==5


def test_draft_batch_retry_publish_and_existing_attempt_snapshots(app,client):
    p=seed();pid=p.id;h=login(client,True)
    attempt=client.post('/api/attempts',json={'paper_id':pid,'mode':'practice'},headers=h).json
    url=f'/api/admin/papers/{pid}/questions/append';data=payload(row(),row('7'))
    created=client.post(url,json=data,headers=h)
    assert created.status_code==201,created.json
    ids=created.json['ids'];assert len(ids)==2
    again=client.post(url,json=data,headers=h)
    assert again.status_code==200 and again.json['ids']==ids and again.json['created']==0
    assert Question.query.count()==7
    assert Question.query.filter_by(status='AVAILABLE').count()==5
    assert QuestionReview.query.filter_by(action='APPEND').count()==2
    q=db.session.get(Question,ids[0]);assert q.evidence['_admin_locked'] and q.answers==['B']
    restored=client.post(f'/api/admin/questions/{q.id}/visibility',json={'updated_at':q.updated_at,'hidden':False},headers=h)
    assert restored.status_code==200
    old=client.get('/api/attempts/'+str(attempt['id'])).json
    assert len(old['palette'])==5
    newer=client.post('/api/attempts',json={'paper_id':pid,'mode':'practice'},headers=h).json
    assert len(newer['palette'])==6
    # Same batch token with edited data cannot accidentally add another copy.
    data['questions'][0]['text']='Changed'
    assert client.post(url,json=data,headers=h).status_code==409


def test_append_all_or_nothing_and_number_conflicts(app,client):
    p=seed();url=f'/api/admin/papers/{p.id}/questions/append';h=login(client,True)
    bad=row('7');bad['answers']=['Z']
    assert client.post(url,json=payload(row(),bad),headers=h).status_code==400
    assert Question.query.count()==5
    assert client.post(url,json=payload(row('1')),headers=h).status_code==409
    assert client.post(url,json=payload(row(),row()),headers=h).status_code==400
    assert client.post(url,json=payload(*[row(str(i+6)) for i in range(21)]),headers=h).status_code==400
    assert Question.query.count()==5


@pytest.mark.parametrize('field,value',[('marks',-1),('marks',True),('answers',['Z']),('text',''),('number',''),('kind','bad')])
def test_invalid_rows_are_rejected(app,client,field,value):
    p=seed();r=row();r[field]=value
    assert client.post(f'/api/admin/papers/{p.id}/questions/append',json=payload(r),headers=login(client,True)).status_code==400
    assert Question.query.count()==5


def test_append_blocked_for_processing_archived_and_alias_papers(app,client):
    p=seed();pid=p.id;h=login(client,True);url=f'/api/admin/papers/{pid}/questions/append'
    batch=IngestionBatch(user_id=User.query.filter_by(role='ADMIN').first().id);db.session.add(batch);db.session.flush()
    f=IngestionFile(batch_id=batch.id,paper_id=pid,filename='x.pdf',status='PROCESSING');db.session.add(f);db.session.commit()
    assert client.post(url,json=payload(row()),headers=h).status_code==409
    f=db.session.get(IngestionFile,f.id);f.status='AVAILABLE';p=db.session.get(Paper,pid);p.status='ARCHIVED';db.session.commit()
    assert client.post(url,json=payload(row()),headers=h).status_code==409
    p=db.session.get(Paper,pid);p.status='AVAILABLE';p.canonical_paper_id=pid;db.session.commit()
    assert client.post(url,json=payload(row()),headers=h).status_code==409


def test_append_published_batch_invalidates_source_snapshot(app,client):
    from backend.paper_content import snapshots
    p=seed();pid=p.id;assert len(snapshots(pid))==5
    response=client.post(f'/api/admin/papers/{pid}/questions/append',json=payload(row(),row('7'),publish=True),headers=login(client,True))
    assert response.status_code==201,response.json
    assert len(snapshots(pid))==7
    assert db.session.get(Paper,pid).status=='AVAILABLE'
