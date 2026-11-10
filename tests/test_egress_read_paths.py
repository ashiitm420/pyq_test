"""Verify repeated public reads avoid transferring question content again."""
from contextlib import contextmanager
from sqlalchemy import event
from backend.models import db,QuestionImage,QuestionOption
from test_study_pages import seed

@contextmanager
def statements():
    rows=[]
    def record(conn,cursor,statement,parameters,context,executemany):rows.append(statement.lower())
    event.listen(db.engine,'before_cursor_execute',record)
    try:yield rows
    finally:event.remove(db.engine,'before_cursor_execute',record)


def test_study_reuses_quiz_snapshots_and_published_solutions(app,client):
    from backend.paper_content import snapshots
    from backend.ai_solutions import _cached_paper_solutions
    c,p,q,s=seed();pid=p.id
    snapshots(pid);_cached_paper_solutions(pid)
    with statements() as sql:
        response=client.get(f'/study/papers/{pid}')
    assert response.status_code==200 and 'PUBLISHED EXPLANATION' in response.text
    assert not any('from question ' in x or 'from question_option' in x or 'from question_image' in x or 'from ai_solution' in x for x in sql)
    q.text='Updated question text';db.session.commit()
    response=client.get(f'/study/papers/{pid}')
    assert 'Updated question text' in response.text and 'PUBLISHED EXPLANATION' not in response.text


def test_public_image_permission_reads_no_question_body_or_children(app,client,monkeypatch):
    import backend.study_pages as pages
    c,p,q,s=seed();image=QuestionImage(question_id=q.id,path='test/image.png');db.session.add(image);db.session.commit();iid=image.id
    monkeypatch.setattr(pages,'image_url',lambda path,id:'https://assets.example.test/image.png')
    with statements() as sql:
        assert client.get(f'/study/images/{iid}').status_code==302
    reads=[x for x in sql if 'from question_image' in x]
    assert len(reads)==1
    assert 'question.text' not in reads[0] and 'question.answers' not in reads[0]
    assert not any('from question_option' in x for x in sql)
    q.evidence={'_active_image_ids':[]};db.session.commit()
    assert client.get(f'/study/images/{iid}').status_code==404
    q.evidence={'_active_image_ids':[iid]};db.session.commit()
    assert client.get(f'/study/images/{iid}').status_code==302
    p.status='ARCHIVED';db.session.commit()
    assert client.get(f'/study/images/{iid}').status_code==404


def test_custom_review_reuses_all_paper_caches_and_revokes_stale_solutions(app):
    from backend.paper_content import snapshots
    from backend.ai_solutions import _cached_paper_solutions,review_solutions
    from backend.models import Paper,Question,AISolution
    from backend.ai_solutions import snapshot,version
    c,p,q,s=seed()
    second=Paper(identity='egress-second',name='Second',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,status='AVAILABLE')
    db.session.add(second);db.session.flush()
    q2=Question(paper_id=second.id,number='1',kind='NAT',text='Second question',status='AVAILABLE');db.session.add(q2);db.session.flush()
    db.session.add(AISolution(question_id=q2.id,version=version(snapshot(q2)),text='Second solution',status='PUBLISHED'));db.session.commit()
    items=[{'question':snapshots(pid)[0]} for pid in (p.id,second.id)]
    for pid in (p.id,second.id):_cached_paper_solutions(pid)
    with statements() as sql:result=review_solutions(items)
    assert all(i['ai_solution']['available'] for i in result)
    assert sql==[]
    s.status='DRAFT';db.session.commit()
    assert not review_solutions(items)[0]['ai_solution']['available']


def test_search_projects_only_preview_columns(app,client):
    c,p,q,s=seed();q.text='Compute '+('long body '*500);q.evidence={'debug':'x'*10000};db.session.commit()
    with statements() as sql:response=client.get('/api/search?q=Compute')
    assert response.status_code==200
    assert len(response.json['questions'][0]['text'])==300
    reads=[x for x in sql if 'substr(question.text' in x]
    assert len(reads)==1 and 'question.evidence' not in reads[0] and 'question.answers' not in reads[0]


def test_admin_question_children_are_batched(app,client):
    from conftest import login
    from backend.models import Question
    c,p,q,s=seed();pid=p.id
    for n in range(3,13):
        row=Question(paper_id=pid,number=str(n),kind='MCQ',text='Batch question',status='AVAILABLE')
        row.options=[QuestionOption(key='a',text='A',position=0),QuestionOption(key='b',text='B',position=1)]
        row.images=[QuestionImage(path=f'test/{n}.png')];db.session.add(row)
    db.session.commit();headers=login(client,admin=True)
    db.session.remove()
    with statements() as sql:response=client.get(f'/api/admin/questions?paper_id={pid}&limit=20',headers=headers)
    assert response.status_code==200
    assert sum('from question_option' in x for x in sql)==1
    assert sum('from question_image' in x for x in sql)==1
