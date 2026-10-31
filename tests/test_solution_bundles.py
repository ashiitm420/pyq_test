import io,json,zipfile
from conftest import login
from test_engine import seed
from test_ai_solutions import output
from backend.models import db,Paper,Question,AISolution

def bundle(client,p):
    q=client.get(f'/api/admin/ai-solutions/papers/{p.id}/export').json['questions'][0]
    return {'format':'pyq-solutions-v1','paper_id':p.id,'solutions':[{'question_id':q['question_id'],'version':q['version'],'output':output()}]}

def test_bundle_zip_and_import(app,client):
    p=seed();h=login(client,True)
    second=Paper(identity='second',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,name='Second',status='AVAILABLE')
    db.session.add(second);db.session.flush()
    q=Question(paper_id=second.id,number='1',kind='MCQ',text='Q',answers=['A'],answer_status='ANSWER_AVAILABLE',status='AVAILABLE',marks=1)
    from backend.models import QuestionOption
    q.options=[QuestionOption(key='A',text='Yes',position=0),QuestionOption(key='B',text='No',position=1)];db.session.add(q);db.session.commit()
    response=client.get(f'/api/admin/ai-solutions/bundle/export?ids={p.id},{second.id}')
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        data=json.loads(z.read('questions.json'));assert len(data['papers'])==2
        assert 'pyq-solutions-bundle-v1' in z.read('BUNDLE_PROMPT.txt').decode()
        assert 'PDF' in z.read('README.txt').decode()
    body={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[bundle(client,p),bundle(client,second)]}}
    preview=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body)
    assert preview.status_code==200 and len(preview.json['papers'])==2
    assert AISolution.query.count()==0
    result=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={**body,'save':True,'publish':True})
    assert result.json['published']==2 and AISolution.query.count()==2
    result=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={**body,'save':True,'publish':True})
    assert result.json['saved']==0 and all(p['error'] for p in result.json['papers'])
    assert client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={**body,'save':True,'publish':True,'replace_existing':True}).json['published']==2

def test_bundle_invalid_paper_does_not_contaminate_valid_paper(app,client):
    p=seed();h=login(client,True);good=bundle(client,p)
    invalid={'format':'pyq-solutions-v1','paper_id':999999,'solutions':good['solutions']}
    r=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[good,invalid]},'save':True,'publish':True})
    assert r.status_code==200 and r.json['published']==1 and r.json['papers'][1]['error']
    assert AISolution.query.count()==1
    assert client.get('/api/admin/ai-solutions/bundle/export?ids=1,1').status_code==400
    assert app.test_client().get('/api/admin/ai-solutions/bundle/export?ids=1').status_code==401

def test_bundle_bad_version_rolls_back_whole_paper_and_flags_stay_drafts(app,client):
    import copy
    p=seed();h=login(client,True);good=bundle(client,p)
    bad=copy.deepcopy(good['solutions'][0]);bad['version']='old';bad['question_id']=Question.query.filter_by(paper_id=p.id,kind='MSQ').first().id
    broken={**good,'solutions':good['solutions']+[bad]}
    r=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[broken]},'save':True,'publish':True})
    assert r.json['saved']==0 and AISolution.query.count()==0
    good['solutions'][0]['output']=output(['B'])
    r=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[good]},'save':True,'publish':True})
    assert r.json['saved']==1 and r.json['published']==0 and r.json['needs_review']==1
    assert AISolution.query.first().status=='NEEDS_REVIEW'

def test_fifty_papers_and_limit(app,client):
    p=seed();h=login(client,True)
    for i in range(49):
        other=Paper(identity=f'bulk-{i}',course_id=p.course_id,term_id=p.term_id,exam_type_id=p.exam_type_id,name=f'Paper {i}',status='AVAILABLE')
        db.session.add(other);db.session.flush()
        db.session.add(Question(paper_id=other.id,number='1',kind='NAT',text='Find two',answers=['2'],answer_status='ANSWER_AVAILABLE',status='AVAILABLE',marks=1))
    db.session.commit()
    ids=[x.id for x in Paper.query.order_by(Paper.id).all()]
    assert len(ids)==50
    r=client.get('/api/admin/ai-solutions/bundle/export?ids='+','.join(map(str,ids)))
    assert r.status_code==200
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        data=json.loads(z.read('questions.json'));assert len(data['papers'])==50
        prompt=z.read('BUNDLE_PROMPT.txt').decode()
        assert 'no fixed step count' in prompt and 'define its symbols' in prompt
    # Unknown papers are isolated, and all 50 entries are accepted by the outer contract.
    papers=[{'paper_id':i,'format':'pyq-solutions-v1','solutions':[]} for i in ids]
    r=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={'bundle':{'format':'pyq-solutions-bundle-v1','papers':papers}})
    assert r.status_code==200 and len(r.json['papers'])==50
    papers.append({'paper_id':99999})
    assert client.post('/api/admin/ai-solutions/bundle/import',headers=h,json={'bundle':{'format':'pyq-solutions-bundle-v1','papers':papers}}).status_code==400
    assert client.get('/api/admin/ai-solutions/bundle/export?ids='+','.join(map(str,ids+[99999]))).status_code==400

def test_retry_exact_saved_content_without_overwrite(app,client):
    p=seed();h=login(client,True);data=bundle(client,p)
    body={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[data]},'save':True,'publish':True,'skip_identical':True}
    assert client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body).json['published']==1
    before=AISolution.query.first().updated_at
    replay=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body).json
    assert replay['saved']==0 and replay['published']==1 and replay['papers'][0]['already_saved']==1
    assert AISolution.query.count()==1 and AISolution.query.first().updated_at==before
    data['solutions'][0]['output']['explanation']='A changed explanation'
    rejected=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body).json
    assert rejected['papers'][0]['error'] and rejected['saved']==0

def test_retry_flagged_solution_stays_unpublished(app,client):
    p=seed();h=login(client,True);data=bundle(client,p);data['solutions'][0]['output']=output(['B'])
    body={'bundle':{'format':'pyq-solutions-bundle-v1','papers':[data]},'save':True,'publish':True,'skip_identical':True}
    client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body)
    r=client.post('/api/admin/ai-solutions/bundle/import',headers=h,json=body).json
    assert r['saved']==0 and r['needs_review']==1 and r['published']==0
    assert AISolution.query.first().status=='NEEDS_REVIEW'
