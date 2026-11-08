import time
from sqlalchemy import event
from conftest import login
from test_engine import seed
from backend.models import db,Paper,Question,QuestionOption,Attempt,AnalyticsEvent,PaperProgress

def papers():
    p=seed();q=Paper(identity='second',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,name='Second paper',status='AVAILABLE')
    db.session.add(q);db.session.flush()
    db.session.add(Question(paper_id=q.id,number='1',kind='MCQ',text='Second question',answers=['B'],answer_status='ANSWER_AVAILABLE',marks=2,negative_marks=.5,status='AVAILABLE',options=[QuestionOption(key='A',text='A',position=0),QuestionOption(key='B',text='B',position=1)]));db.session.commit();return p,q

def test_custom_exam_admin_only_order_grading_deadline_and_no_analytics(app,client):
    p,q=papers();h=login(client)
    body={'paper_ids':[q.id,p.id],'mode':'exam','duration_seconds':600}
    assert client.post('/api/attempts?bootstrap=1',headers=h,json=body).status_code==403
    h=login(client,True)
    r=client.post('/api/attempts?bootstrap=1',headers=h,json=body);assert r.status_code==201,r.json
    a=r.json;aid=a['id'];assert a['custom_exam'] and len(a['items'])==6
    assert a['papers'][0]['id']==q.id and a['palette'][0]['paper_id']==q.id
    assert all('answers' not in row['question'] and 'explanation' not in row['question'] and 'feedback' not in row for row in a['items'])
    assert client.get(f'/api/attempts/{aid}?bootstrap=1').json['palette'][0]['paper_id']==q.id
    assert client.post(f'/api/attempts/{aid}/switch-mode',headers=h,json={'mode':'practice'}).status_code==200
    assert client.post(f'/api/attempts/{aid}/switch-mode',headers=h,json={'mode':'exam'}).status_code==200
    qid=a['palette'][0]['question_id']
    assert client.post(f'/api/attempts/{aid}/answers',headers=h,json={'question_id':qid,'answer':['B']}).status_code==200
    d=client.post(f'/api/attempts/{aid}/submit',headers=h).json
    assert d['result']['score']==2 and d['result']['papers'][0]['score']==2
    assert d['result']['papers'][1]['score']==0 and not d['records_progress']
    assert client.post(f'/api/attempts/{aid}/submit',headers=h).json['result']==d['result']
    assert AnalyticsEvent.query.count()==PaperProgress.query.count()==0
    assert client.get(f'/api/attempts/{aid}/review').status_code==200
    with client.session_transaction() as session:session.pop('uid',None)
    for endpoint in [f'/api/attempts/{aid}',f'/api/attempts/{aid}/status',f'/api/attempts/{aid}/review',f'/api/attempts/{aid}/questions/{qid}']:
        assert client.get(endpoint).status_code==403,endpoint
    assert client.post(f'/api/attempts/{aid}/submit',headers=h).status_code==403
    assert client.post(f'/api/attempts/{aid}/answers',headers=h,json={'question_id':qid,'answer':['A']}).status_code==403

def test_custom_limits_reject_without_replacing_active_attempt(app,client):
    p,q=papers();h=login(client,True)
    active=client.post('/api/attempts',headers=h,json={'paper_id':p.id}).json['id']
    for ids,duration in [([],60),([p.id,p.id],60),([True],60),([p.id]*5,60),([p.id],True),([p.id],0),([p.id],28801),([p.id],60.5)]:
        assert client.post('/api/attempts',headers=h,json={'paper_ids':ids,'duration_seconds':duration}).status_code==400
    assert db.session.get(Attempt,active).status=='ACTIVE'
    alias=Paper(identity='alias',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,name='Alias',status='AVAILABLE',canonical_paper_id=p.id);db.session.add(alias);db.session.commit()
    assert client.post('/api/attempts',headers=h,json={'paper_ids':[p.id,alias.id],'duration_seconds':60}).status_code==400
    for n in range(100):db.session.add(Question(paper_id=q.id,number=str(n+2),kind='NAT',text='x',status='AVAILABLE'))
    db.session.commit()
    assert client.post('/api/attempts',headers=h,json={'paper_ids':[q.id],'duration_seconds':60}).status_code==400
    assert db.session.get(Attempt,active).status=='ACTIVE'

def test_custom_timeout_does_not_accept_late_answers(app,client):
    p,q=papers();h=login(client,True)
    a=client.post('/api/attempts',headers=h,json={'paper_ids':[q.id],'duration_seconds':60}).json
    row=db.session.get(Attempt,a['id']);row.deadline=time.time()-1;db.session.commit()
    d=client.post(f"/api/attempts/{a['id']}/submit",headers=h,json={'items':[{'question_id':a['palette'][0]['question_id'],'answer':['B']}]}).json
    assert d['result']['score']==0 and d['result']['papers'][0]['skipped']==1

def test_custom_content_limit_and_cached_snapshots_unchanged(app,client):
    from backend.paper_content import snapshots
    p,q=papers();h=login(client,True)
    cached=snapshots(p.id);before=repr(cached)
    r=client.post('/api/attempts?bootstrap=1',headers=h,json={'paper_ids':[p.id,q.id],'duration_seconds':60})
    assert r.status_code==201 and repr(cached)==before
    aid=r.json['id'];deadline=r.json['deadline'];qid=r.json['palette'][0]['question_id']
    before_queries=[]
    def capture(conn,cursor,statement,parameters,context,executemany):before_queries.append(statement)
    event.listen(db.engine,'before_cursor_execute',capture)
    try:
        assert client.get(f'/api/attempts/{aid}/status').json['deadline']==deadline
    finally:event.remove(db.engine,'before_cursor_execute',capture)
    assert not any('attempt_answer' in sql.lower() for sql in before_queries)
    # Oversized source text rejected before deleting an existing active attempt.
    question=Question.query.filter_by(paper_id=q.id).one();question.text='x'*(1024*1024+1);db.session.commit()
    assert client.post('/api/attempts',headers=h,json={'paper_ids':[q.id],'duration_seconds':60}).status_code==400
    assert db.session.get(Attempt,aid).status=='ACTIVE'


def test_custom_practice_switch_preserves_time_budget_and_answers(app,client,monkeypatch):
    p,q=papers();h=login(client,True)
    a=client.post('/api/attempts?bootstrap=1',headers=h,json={'paper_ids':[q.id],'mode':'practice','duration_seconds':600}).json
    aid=a['id'];qid=a['palette'][0]['question_id'];assert a['mode']=='practice' and a['deadline'] is None
    assert client.post(f'/api/attempts/{aid}/answers',headers=h,json={'question_id':qid,'answer':['B']}).status_code==200
    timed=client.post(f'/api/attempts/{aid}/switch-mode',headers=h,json={'mode':'exam','duration_seconds':28800}).json
    assert 598<=timed['deadline']-timed['server_time']<=600
    row=db.session.get(Attempt,aid);row.deadline=time.time()+120;db.session.commit()
    paused=client.post(f'/api/attempts/{aid}/switch-mode',headers=h,json={'mode':'practice'}).json
    assert paused['deadline'] is None and paused['feedback'][0]['feedback']['outcome']=='CORRECT'
    resumed=client.post(f'/api/attempts/{aid}/switch-mode',headers=h,json={'mode':'exam','duration_seconds':28800}).json
    assert 118<=resumed['deadline']-resumed['server_time']<=120
    assert client.get(f'/api/attempts/{aid}/questions/{qid}').json['answer']==['B']
    assert 'feedback' not in client.get(f'/api/attempts/{aid}/questions/{qid}').json
    assert client.post(f'/api/attempts/{aid}/submit',headers=h).json['result']['score']==2
    assert AnalyticsEvent.query.count()==0


def test_custom_exam_direct_route_loads_spa_shell(app,client):
    r=client.get('/custom-exam')
    assert r.status_code==200
    assert 'noindex' in r.headers['X-Robots-Tag']
    assert b'id="app"' in r.data
    assert client.get('/custom-exam-invalid').status_code==404
