"""Local synthetic evidence only; never a production capacity/load test."""
import json,time,tracemalloc
from sqlalchemy import event
from conftest import login
from test_engine import seed
from backend.models import db,Paper,Question,QuestionOption
from backend.paper_content import snapshots

def test_equal_question_count_budget(app,client):
    base=seed();QuestionOption.query.delete();Question.query.delete();db.session.flush()
    parts=[]
    for n in range(4):
        p=Paper(identity='budget'+str(n),name='Budget paper '+str(n),course_id=base.course_id,term_id=base.term_id,exam_type_id=base.exam_type_id,status='AVAILABLE');db.session.add(p);db.session.flush();parts.append(p)
    for p,count in [(base,80)]+[(p,20) for p in parts]:
        for n in range(count):db.session.add(Question(paper_id=p.id,number=str(n+1),kind='NAT',text='Synthetic numeric question',answers=2,answer_status='ANSWER_AVAILABLE',marks=1,negative_marks=0,status='AVAILABLE'))
    db.session.commit();h=login(client,True)
    for pid in [base.id]+[p.id for p in parts]:snapshots(pid)
    evidence={}
    for label,body in [('single_80',{'paper_id':base.id,'mode':'exam','duration_seconds':600}),('custom_4x20',{'paper_ids':[p.id for p in parts],'mode':'exam','duration_seconds':600})]:
        sql=[]
        def capture(conn,cursor,statement,parameters,context,executemany):sql.append(statement)
        event.listen(db.engine,'before_cursor_execute',capture)
        tracemalloc.start();cpu=time.process_time();wall=time.perf_counter()
        try:
            r=client.post('/api/attempts?bootstrap=1',headers=h,json=body)
            elapsed=time.perf_counter()-wall;cpu=time.process_time()-cpu;_,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop();event.remove(db.engine,'before_cursor_execute',capture)
        assert r.status_code==201 and len(r.json['items'])==80
        evidence[label]=dict(app_ms=round(elapsed*1000,1),cpu_ms=round(cpu*1000,1),python_peak_kib=round(peak/1024),sql_statements=len(sql),response_kib=round(len(r.data)/1024,1))
        aid=r.json['id'];qid=r.json['palette'][0]['question_id'];sql=[]
        event.listen(db.engine,'before_cursor_execute',capture)
        try:
            saved=client.post(f'/api/attempts/{aid}/answers',headers=h,json={'question_id':qid,'answer':'2'})
            assert saved.status_code==200
        finally:event.remove(db.engine,'before_cursor_execute',capture)
        evidence[label]['save_sql_statements']=len(sql)
    assert evidence['custom_4x20']['save_sql_statements']==evidence['single_80']['save_sql_statements']
    assert evidence['custom_4x20']['sql_statements']<=evidence['single_80']['sql_statements']+6
    print('\nLOCAL_SYNTHETIC_BUDGET '+json.dumps(evidence,sort_keys=True))
