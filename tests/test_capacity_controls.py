import threading
from backend.models import db,Attempt
from conftest import login
from test_production_stability import seed

def test_hashed_assets_do_not_read_or_refresh_session(app,client):
    from pathlib import Path
    dist=Path(app.config['FRONTEND_DIST']);(dist/'assets').mkdir()
    (dist/'assets/app-abcdefgh.js').write_text('export const value=1;')
    login(client,admin=True)
    for _ in range(2):
        r=client.get('/assets/app-abcdefgh.js')
        assert r.status_code==200
        assert 'Cookie' not in r.headers.get('Vary','')
        assert 'Set-Cookie' not in r.headers
        assert 'immutable' in r.headers['Cache-Control']
    assert client.get('/api/session').json['user']['role']=='ADMIN'
    assert client.get('/api/session').headers['Cache-Control']=='no-store'

def test_start_gate_has_no_queue_and_releases_after_failure(app,client):
    slots=app.extensions['exam_start_slots'];slots.acquire();slots.acquire()
    try:
        r=client.post('/api/attempts',json={})
        assert r.status_code==503 and r.json['code']=='START_BUSY'
        assert r.headers['Retry-After']=='3'
        assert Attempt.query.count()==0
    finally:slots.release();slots.release()
    h=login(client)
    assert client.post('/api/attempts',headers=h,json={'mode':'invalid'}).status_code==400
    assert slots.acquire(blocking=False);assert slots.acquire(blocking=False)
    slots.release();slots.release()

def test_exam_priority_is_admin_only_and_pauses_heavy_requests(app,client):
    h=login(client)
    assert client.post('/api/admin/exam-priority',headers=h,json={'enabled':True}).status_code==401
    h=login(client,admin=True)
    assert client.post('/api/admin/exam-priority',headers=h,json={'enabled':True}).json['enabled']
    r=client.post('/api/admin/upload-pyq',headers=h)
    assert r.status_code==409 and r.json['code']=='EXAM_PRIORITY'
    assert client.get('/api/home').status_code==200
    assert not client.post('/api/admin/exam-priority',headers=h,json={'enabled':False}).json['enabled']

def test_resume_keeps_owned_answers_and_deadline(app,client):
    pid=seed(1)[0];h=login(client)
    a=client.post('/api/attempts?bootstrap=1',headers=h,json={'paper_id':pid,'mode':'exam','duration_seconds':600}).json
    qid=a['items'][0]['question']['id']
    assert client.post(f'/api/attempts/{a["id"]}/answers',headers=h,json={'question_id':qid,'marked':True}).status_code==200
    resumed=client.get(f'/api/attempts/{a["id"]}?bootstrap=1').json
    assert resumed['deadline']==a['deadline'] and resumed['items'][0]['marked']
    assert 'answers' not in resumed['items'][0]['question']
    stranger=app.test_client();stranger.get('/api/session')
    assert stranger.get(f'/api/attempts/{a["id"]}?bootstrap=1').status_code==404


def test_expired_resume_cannot_submit_unsent_answers(app,client):
    import time
    from backend.models import AttemptAnswer
    pid=seed(1)[0];h=login(client)
    a=client.post('/api/attempts?bootstrap=1',headers=h,json={'paper_id':pid,'mode':'exam','duration_seconds':600}).json
    attempt=db.session.get(Attempt,a['id']);attempt.deadline=time.time()-1;db.session.commit()
    qid=a['items'][0]['question']['id']
    r=client.post(f'/api/attempts/{a["id"]}/submit',headers=h,json={'items':[{'question_id':qid,'answer':['A']}]})
    assert r.status_code==200 and r.json['status']=='SUBMITTED'
    assert AttemptAnswer.query.filter_by(attempt_id=a['id'],question_id=qid).one().answer is None
