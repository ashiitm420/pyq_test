from conftest import login
from backend.models import db, ContactMessage, FeedbackLike


def post(client,headers):
    r=client.post('/api/feedback',json={'name':'Student','stars':5,'message':'Very useful practice!'},headers=headers)
    assert r.status_code==201
    return r.json['items'][0]['id']


def test_receipt_state_private_and_not_shared_in_list(client,app):
    h=login(client)
    assert client.get('/api/feedback/state').json=={'submitted':False,'liked_ids':[]}
    id=post(client,h)
    assert client.get('/api/feedback/state').json['submitted'] is True
    other=app.test_client();login(other)
    assert other.get('/api/feedback/state').json['submitted'] is False
    public=client.get('/api/feedback').json
    assert public['items'][0]['id']==id
    assert 'guest_hash' not in str(public) and 'submitted' not in public
    assert client.get('/api/feedback/state').headers['Cache-Control']=='no-store'
    # Moderation does not cause a previous author to be asked for feedback again.
    row=db.session.get(ContactMessage,id);row.status='RESOLVED';db.session.commit()
    assert client.get('/api/feedback/state').json['submitted'] is True


def test_idempotent_likes_and_browser_isolation(client,app):
    h=login(client);id=post(client,h);url=f'/api/feedback/{id}/like'
    for _ in range(3):
        r=client.put(url,headers=h)
        assert r.status_code==200 and r.json['likes']==1 and r.json['liked']
    other=app.test_client();oh=login(other)
    assert other.put(url,headers=oh).json['likes']==2
    assert client.get('/api/feedback/state').json['liked_ids']==[id]
    assert client.get('/api/feedback').json['items'][0]['likes']==2
    for _ in range(2):assert client.delete(url,headers=h).json['likes']==1
    assert client.get('/api/feedback/state').json['liked_ids']==[]
    assert other.get('/api/feedback/state').json['liked_ids']==[id]
    assert FeedbackLike.query.count()==1


def test_hidden_contact_and_csrf_not_likeable(client):
    h=login(client);id=post(client,h);url=f'/api/feedback/{id}/like'
    assert client.put(url).status_code==403
    row=db.session.get(ContactMessage,id);row.status='RESOLVED';db.session.commit()
    assert client.put(url,headers=h).status_code==404
    row.status='OPEN';row.topic='General enquiry';db.session.commit()
    assert client.put(url,headers=h).status_code==404
    assert client.put('/api/feedback/999999/like',headers=h).status_code==404


def test_likes_do_not_flush_paper_or_catalog_cache(client):
    from backend.content_cache import cached, forget
    h=login(client);id=post(client,h);calls=[]
    keys=['all-visible-papers','paper:3:snapshots:msq-proportional-v1','paper-published-solutions:3','admin-solution-summary:test']
    for key in keys:cached(key,lambda:calls.append(key) or ['keep'])
    assert client.put(f'/api/feedback/{id}/like',headers=h).status_code==200
    for key in keys:assert cached(key,lambda:None)==['keep']
    assert len(calls)==len(keys)
    for key in keys:forget(key)
