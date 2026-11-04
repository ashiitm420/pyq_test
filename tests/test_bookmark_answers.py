from backend.models import db,Course,Term,ExamType,Paper,Question,AISolution
from backend.ai_solutions import snapshot,version


def seed():
    c=Course(name='Maths',code='MA1');t=Term(name='May 2026',year=2026,month=5);e=ExamType(name='Quiz 1')
    db.session.add_all([c,t,e]);db.session.flush()
    p=Paper(identity='bm-answers',name='Maths Quiz 1',course_id=c.id,term_id=t.id,exam_type_id=e.id,status='AVAILABLE')
    db.session.add(p);db.session.flush()
    q=Question(paper_id=p.id,number='1',kind='NAT',text='2+2?',answers=4,answer_status='ANSWER_AVAILABLE',explanation='Add them.',status='AVAILABLE')
    other=Question(paper_id=p.id,number='2',kind='NAT',text='3+3?',answers=6,answer_status='ANSWER_AVAILABLE',status='AVAILABLE')
    hidden=Question(paper_id=p.id,number='3',kind='NAT',text='secret',answers=9,answer_status='ANSWER_AVAILABLE',status='HIDDEN')
    db.session.add_all([q,other,hidden]);db.session.flush()
    db.session.add(AISolution(question_id=q.id,version=version(snapshot(q)),text='Worked solution',status='PUBLISHED'))
    db.session.commit()
    return p,q,other,hidden


def test_bookmark_answers_return_only_requested_visible_questions(client):
    p,q,other,hidden=seed()
    r=client.get(f'/api/papers/{p.id}/answers?ids={q.id},{hidden.id}')
    assert r.status_code==200
    items=r.get_json()['items']
    assert [i['id'] for i in items]==[q.id]
    assert items[0]['answers']==4 and items[0]['explanation']=='Add them.' and items[0]['solution']=='Worked solution'
    assert client.get(f'/api/papers/{p.id}/answers?ids={other.id}').get_json()['items'][0]['solution'] is None


def test_bookmark_answers_validate_input(client):
    p,q,_,_=seed()
    assert client.get(f'/api/papers/{p.id}/answers').status_code==400
    assert client.get(f'/api/papers/{p.id}/answers?ids=a,b').status_code==400
    assert client.get(f'/api/papers/{p.id}/answers?ids='+','.join(['1']*101)).status_code==400
    p.status='ARCHIVED';db.session.commit()
    assert client.get(f'/api/papers/{p.id}/answers?ids={q.id}').status_code==404
