from backend.models import db,Course,Term,ExamType,Paper,Question,QuestionOption,QuestionImage,AISolution
from backend.engine import question_snapshot
from backend.ai_solutions import version,snapshot
from conftest import login

EVIDENCE={'answer_indicators':['x'*5000],'answer_source':'key','shared_passage_text':'Read this passage.',
          'subquestion_text':'Which is right?','shared_passage':True,'layout_assets':{'img1':{'width':40}},'_admin_locked':True}

def seed():
    c=Course(name='Maths',code='MA1');t=Term(name='May 2026',year=2026,month=5);e=ExamType(name='Quiz 1')
    db.session.add_all([c,t,e]);db.session.flush()
    p=Paper(identity='slim',name='Maths Quiz 1',course_id=c.id,term_id=t.id,exam_type_id=e.id,status='AVAILABLE');db.session.add(p);db.session.flush()
    q=Question(paper_id=p.id,number='1',kind='MCQ',text='full text',answers=['b'],answer_status='ANSWER_AVAILABLE',marks=2,negative_marks=0,status='AVAILABLE',evidence=dict(EVIDENCE))
    q.options=[QuestionOption(key='a',text='A',position=0),QuestionOption(key='b',text='B',position=1)]
    q.images=[QuestionImage(path='pyq/img1.png',alt='diagram')]
    plain=Question(paper_id=p.id,number='2',kind='NAT',text='2+2',answers=4,answer_status='ANSWER_AVAILABLE',marks=1,negative_marks=0,status='AVAILABLE',evidence={})
    db.session.add_all([q,plain]);db.session.commit()
    return p,q,plain

def full_snapshots(p):
    db.session.expire_all()
    return {q.id:question_snapshot(q) for q in Question.query.filter_by(paper_id=p.id,status='AVAILABLE')}

def test_paper_snapshots_match_full_rows_and_never_leak_partial_evidence(app):
    from backend.paper_content import snapshots
    p,q,plain=seed();expected=full_snapshots(p);db.session.expunge_all()
    got={s['id']:s for s in snapshots(p.id)}
    assert got==expected
    assert got[q.id]['passage']=='Read this passage.' and got[q.id]['images'][0]['width']==40
    # A later edit in the same request must still see and keep the full evidence.
    again=db.session.get(Question,q.id);again.marks=3;db.session.commit()
    db.session.expire_all()
    assert db.session.get(Question,q.id).evidence==EVIDENCE

def test_solution_summary_counts_with_slim_rows(app,client):
    p,q,plain=seed()
    db.session.add_all([AISolution(question_id=q.id,version=version(snapshot(q)),text='ok',status='PUBLISHED'),
                        AISolution(question_id=plain.id,version='old',text='old',status='DRAFT')]);db.session.commit()
    pid,qid=p.id,q.id;db.session.expunge_all()
    h=login(client,admin=True)
    d=client.get('/api/admin/ai-solutions/summary',headers=h).get_json()
    row=next(x for x in d['papers'] if x['id']==p.id)
    assert (row['uploaded'],row['published'],row['outdated'])==(1,1,1)
    db.session.expire_all()
    assert db.session.get(Question,qid).evidence==EVIDENCE


def test_question_and_solution_writes_only_drop_their_own_paper(app):
    from backend.paper_content import snapshots
    from backend import paper_content
    from backend.content_cache import _local_cache
    p,q,plain=seed()
    e=ExamType.query.first();other=Paper(identity='other',name='Other',course_id=p.course_id,term_id=p.term_id,exam_type_id=e.id,status='AVAILABLE')
    db.session.add(other);db.session.flush()
    oq=Question(paper_id=other.id,number='1',kind='NAT',text='other',answers=1,answer_status='ANSWER_AVAILABLE',marks=1,negative_marks=0,status='AVAILABLE',evidence={})
    db.session.add(oq);db.session.commit()
    key=lambda pid:'paper:'+str(pid)+':snapshots:msq-proportional-v1'
    snapshots(p.id);snapshots(other.id)
    assert key(p.id) in _local_cache and key(other.id) in _local_cache
    q.marks=5;db.session.commit()
    assert key(p.id) not in _local_cache and key(other.id) in _local_cache
    assert next(s for s in snapshots(p.id) if s['id']==q.id)['marks']==5
    # An option edited through its own row still finds the paper.
    opt=QuestionOption.query.filter_by(question_id=q.id,key='a').one();opt.text='A2';db.session.commit()
    assert key(p.id) not in _local_cache and key(other.id) in _local_cache
    snapshots(p.id)
    db.session.add(AISolution(question_id=oq.id,version='v',text='x',status='DRAFT'));db.session.commit()
    assert key(p.id) in _local_cache and key(other.id) not in _local_cache
    # Deleting a question also drops its paper.
    snapshots(other.id);db.session.delete(plain);db.session.commit()
    assert key(p.id) not in _local_cache and key(other.id) in _local_cache


def test_image_reassignment_and_expired_question_move_invalidate_both_papers(app):
    from backend.paper_content import snapshots
    from backend.content_cache import _local_cache
    p,q,plain=seed()
    other=Paper(identity='move',name='Other',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,status='AVAILABLE')
    db.session.add(other);db.session.flush()
    oq=Question(paper_id=other.id,number='1',kind='NAT',text='Other',answers=1,marks=1,status='AVAILABLE')
    db.session.add(oq);db.session.commit()
    key=lambda pid:'paper:'+str(pid)+':snapshots:msq-proportional-v1'
    snapshots(p.id);snapshots(other.id)
    image=q.images[0];image.question_id=oq.id;db.session.commit()
    assert key(p.id) not in _local_cache and key(other.id) not in _local_cache
    assert not next(x for x in snapshots(p.id) if x['id']==q.id)['images']
    assert snapshots(other.id)[0]['images']
    db.session.expire(plain,['paper_id']);plain.paper_id=other.id;db.session.commit()
    assert key(p.id) not in _local_cache and key(other.id) not in _local_cache
    assert plain.id in [x['id'] for x in snapshots(other.id)]


def test_rollback_and_outer_transaction_survive_slim_read(app):
    from backend.paper_content import snapshots
    from backend.content_cache import _local_cache
    p,q,plain=seed();key='paper:'+str(p.id)+':snapshots:msq-proportional-v1'
    snapshots(p.id);q.marks=9;db.session.flush();db.session.rollback()
    assert key in _local_cache
    assert next(x for x in snapshots(p.id) if x['id']==q.id)['marks']==2
    # Read-only slim session must not roll back the request's pending writes.
    q.marks=4;db.session.flush()
    from backend.content_cache import forget
    forget(key);assert next(x for x in snapshots(p.id) if x['id']==q.id)['marks']==4
    db.session.commit();db.session.expire_all();assert db.session.get(Question,q.id).marks==4


def test_targeted_forget_fences_inflight_fills_local_and_redis(app,monkeypatch):
    import fakeredis
    from backend import content_cache as cache
    for redis in (None,fakeredis.FakeRedis(decode_responses=True)):
        cache._local_clear();monkeypatch.setattr(cache,'client',lambda:redis)
        key='paper:123:snapshots:msq-proportional-v1'
        def load_old():cache.forget(key);return ['old']
        assert cache.cached(key,load_old)==['old']
        assert cache._local_get(key) is None
        assert cache.cached(key,lambda:['new'])==['new']
        assert cache.cached(key,lambda:['bad'])==['new']
        if redis is not None:
            epoch=redis.get(cache.prefix()+':epoch:snapshots')
            assert redis.get(cache.prefix()+':'+epoch+':'+key)=='[\"new\"]'


def test_bulk_update_falls_back_to_safe_scope_invalidation(app):
    from backend.paper_content import snapshots
    p,q,plain=seed();snapshots(p.id)
    db.session.query(Question).filter_by(id=q.id).update({'answers':['a']},synchronize_session=False);db.session.commit()
    assert next(x for x in snapshots(p.id) if x['id']==q.id)['answers']==['a']


def test_slim_read_does_not_fetch_debug_evidence_or_extra_pool_connection(app):
    from sqlalchemy import event
    from backend.paper_content import snapshots
    p,q,plain=seed();db.session.connection();statements=[];checkouts=[]
    def sql(conn,cursor,statement,parameters,context,executemany):statements.append(statement)
    def checkout(*args):checkouts.append(1)
    event.listen(db.engine,'before_cursor_execute',sql);event.listen(db.engine,'checkout',checkout)
    try:snapshots(p.id)
    finally:event.remove(db.engine,'before_cursor_execute',sql);event.remove(db.engine,'checkout',checkout)
    assert not checkouts
    # JSON projection is selected; the unfiltered evidence column is not.
    assert any('JSON_QUOTE(JSON_EXTRACT(question.evidence' in s for s in statements)
    assert not any('question.evidence AS question_evidence' in s for s in statements)


def test_other_process_redis_invalidation_cannot_seed_local_fallback(app,monkeypatch):
    import fakeredis
    from backend import content_cache as cache
    redis=fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache,'client',lambda:redis);cache._local_clear()
    key='paper:999:snapshots:msq-proportional-v1'
    def concurrent_change():
        # A second process changes only Redis, not this process generation.
        redis.set(cache.prefix()+':forgot:'+key,'new-token')
        return ['old']
    assert cache.cached(key,concurrent_change)==['old']
    assert cache._local_get(key) is None
    assert cache.cached(key,lambda:['new'])==['new']
