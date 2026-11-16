import copy,json
import pytest
from backend.models import db,Question,QuestionReview,IngestionFile,IngestionBatch,User,ImportRun,AttemptAnswer
from backend.verified_key_repair import apply_verified_keys,REPAIR_ID
from backend.engine import grade
from backend.paper_content import snapshots
from conftest import login
from test_engine import seed


def prepare(tmp_path):
 p=seed();q=Question.query.filter_by(paper_id=p.id,kind='NAT').one()
 batch=IngestionBatch(user_id=User.query.filter_by(role='ADMIN').first().id);db.session.add(batch);db.session.flush()
 f=IngestionFile(batch_id=batch.id,paper_id=p.id,filename='source.pdf',path='source.pdf',status='AVAILABLE');db.session.add(f);db.session.flush()
 q.ingestion_file_id=f.id;q.answers=None;q.answer_status='ANSWER_UNAVAILABLE';q.evidence={'source_question_id':'12345678','keep':'original evidence'};q.warnings=['ANSWER_UNAVAILABLE','UNPARSED_NUMERIC_KEY:9 to 10\nSPG','KEEP_ME'];db.session.commit()
 key={'kind':'range','raw':'9 to 10','lower':'9','upper':'10','inclusive':True}
 row={'id':q.id,'paper_id':p.id,'ingestion_file_id':f.id,'number':q.number,'kind':q.kind,'marks':q.marks,'source_question_id':'12345678','expected_updated_at':q.updated_at,'old_answers':None,'old_answer_status':'ANSWER_UNAVAILABLE','answers':key,'raw_key':'9 to 10','source_pdf_sha256':'a'*64,'verification':'test source'}
 path=tmp_path/'manifest.json';path.write_text(json.dumps({'repair_id':REPAIR_ID,'questions':[row]}))
 return p,q,f,row,path


def test_idempotent_audited_targeted_repair_preserves_snapshots_and_other_fields(app,client,tmp_path):
 p,q,f,row,path=prepare(tmp_path)
 old_text=q.text;old_marks=q.marks;old_evidence=copy.deepcopy(q.evidence)
 before=next(s for s in snapshots(p.id) if s['id']==q.id);assert before['answer_status']=='ANSWER_UNAVAILABLE'
 h=login(client);a=client.post('/api/attempts',json={'paper_id':p.id,'mode':'practice'},headers=h).json
 result=apply_verified_keys(path);assert result['updated']==1
 db.session.expire_all();q=db.session.get(Question,q.id)
 assert q.text==old_text and q.marks==old_marks and q.evidence['keep']==old_evidence['keep']
 assert q.warnings==['KEEP_ME'] and q.evidence['_admin_locked'] is True
 history=QuestionReview.query.filter_by(question_id=q.id).one();assert history.action=='SOURCE_KEY_REPAIR' and history.before['answers'] is None and history.after['answers']==row['answers']
 assert apply_verified_keys(path)=={'already_applied':True,'updated':0};assert QuestionReview.query.count()==1
 assert Question.query.filter_by(paper_id=p.id,kind='SUBJECTIVE').one().answers is None
 assert db.session.query(AttemptAnswer).filter_by(attempt_id=a['id'],question_id=q.id).one().snapshot['answer_status']=='ANSWER_UNAVAILABLE'
 fresh=next(s for s in snapshots(p.id) if s['id']==q.id)
 assert grade(fresh,'9.5')['outcome']=='CORRECT' and grade(fresh,'11')['outcome']=='INCORRECT'
 # Existing undo restores the previous key; the startup receipt prevents reapplying it.
 ah=login(client,True);r=client.post(f'/api/admin/questions/{q.id}/undo',json={'updated_at':q.updated_at},headers=ah)
 assert r.status_code==200;assert db.session.get(Question,q.id).answers is None
 assert apply_verified_keys(path)['already_applied'] is True


@pytest.mark.parametrize('changed',['locked','updated','kind','archived','processing'])
def test_stale_manual_changed_and_processing_questions_are_skipped(app,tmp_path,changed):
 p,q,f,row,path=prepare(tmp_path)
 if changed=='locked':q.evidence={**q.evidence,'_admin_locked':True}
 elif changed=='updated':q.updated_at+=1
 elif changed=='kind':q.kind='SUBJECTIVE'
 elif changed=='archived':p.status='ARCHIVED'
 else:f.status='PROCESSING'
 db.session.commit();r=apply_verified_keys(path)
 assert r['updated']==0 and r['skipped']==1 and q.answers is None
 assert QuestionReview.query.count()==0


def test_invalid_manifest_rolls_back_and_does_not_record_success(app,tmp_path):
 p,q,f,row,path=prepare(tmp_path);row['answers']['upper']='999'
 path.write_text(json.dumps({'repair_id':REPAIR_ID,'questions':[row]}))
 with pytest.raises(ValueError):apply_verified_keys(path)
 assert db.session.get(Question,q.id).answers is None
 assert QuestionReview.query.count()==0 and ImportRun.query.count()==0


def test_bundled_manifest_excludes_subjective_and_has_only_source_matching_keys():
 from backend.verified_key_repair import MANIFEST
 from backend.numeric import parse_numeric_answer_block
 data=json.loads(MANIFEST.read_text());assert len(data['questions'])==200
 for r in data['questions']:
  assert r['kind'] in ('NAT','MSQ') and r['old_answer_status']=='ANSWER_UNAVAILABLE'
  if r['kind']=='NAT':assert parse_numeric_answer_block(r['raw_key'])==r['answers']


def test_industry_pilot_keys_score_at_their_original_marks():
 from backend.verified_key_repair import MANIFEST
 data=json.loads(MANIFEST.read_text());byid={r['id']:r for r in data['questions']}
 cases={20026:('16','17'),21354:('2700','2701'),22276:('9.5','9.7'),22544:('4','5'),24562:('300','301'),26918:('21875','22095'),27876:('-33','-29'),28603:('114','115')}
 for qid,(right,wrong) in cases.items():
  r=byid[qid];s={'kind':r['kind'],'answers':r['answers'],'answer_status':'ANSWER_AVAILABLE','marks':r['marks'],'negative_marks':0,'tolerance':0}
  assert grade(s,right)=={'outcome':'CORRECT','awarded':r['marks']}
  assert grade(s,wrong)=={'outcome':'INCORRECT','awarded':0}
