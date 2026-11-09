import {it,expect,afterEach,vi} from 'vitest';
import {createPaperInsights,readPaperInsights,paperResultRows} from '../src/paperInsights';
afterEach(()=>sessionStorage.clear());
const attempt=()=>({id:1,expires_at:Date.now()/1000+3600,server_time:10,started_at:10,papers:[{source_paper_id:5},{source_paper_id:6}],palette:[{question_id:11,paper_id:5,state:'ANSWERED_AND_MARKED_FOR_REVIEW',marked:true},{question_id:12,paper_id:5,state:'NOT_ANSWERED'},{question_id:21,paper_id:6,state:'ANSWERED'}],result:{papers:[{id:1,source_paper_id:5,score:2,total_marks:4},{id:2,source_paper_id:6,score:1,total_marks:2}]}});
it('attributes visible time to each paper, excludes hidden time, and survives refresh without counting the gap',()=>{
 let t=0;const a=attempt(),tracker=createPaperInsights(a,{now:()=>t});tracker.active(5);t=10000;tracker.active(6);t=30000;tracker.active(6,false);t=90000;tracker.active(6,true);t=95000;tracker.checkpoint();
 const before=readPaperInsights(a);expect(before.time).toEqual({'5':10000,'6':25000});
 t=200000;const restored=createPaperInsights(a,{now:()=>t});restored.active(5);t+=5000;restored.finish();
 expect(readPaperInsights(a).time).toEqual({'5':15000,'6':25000});
});
it('caps exam time at deadline and freezes completed timing',()=>{
 let t=0;const a=attempt(),tracker=createPaperInsights(a,{now:()=>t});tracker.deadline(10);tracker.active(5);t=15000;tracker.finish();t=50000;tracker.active(6);tracker.checkpoint();expect(readPaperInsights(a).time).toEqual({'5':10000,'6':0});
});
it('counts only explicitly unsure answered questions, preserves server marks, and shows missing historical metrics as unavailable',()=>{
 const a=attempt(),tracker=createPaperInsights(a);tracker.toggle(11);tracker.toggle(12);tracker.toggle(999);const data=readPaperInsights(a);expect(data.unsure).toEqual([11,12]);
 const rows=paperResultRows(a,data);expect(rows[0]).toMatchObject({score:2,total_marks:4,marked:1,unsure:1});expect(rows[1].unsure).toBe(0);
 expect(paperResultRows(a,null)[0]).toMatchObject({active_seconds:null,unsure:null,marked:1});tracker.toggle(11);expect(readPaperInsights(a).unsure).toEqual([12]);
});
it('bounds temporary records and tolerates unavailable storage',()=>{
 for(let i=0;i<15;i++)sessionStorage.setItem('pyq-paper-insights-v1-'+(i+10),JSON.stringify({version:1,expiresAt:Date.now()+3600000}));
 createPaperInsights(attempt());expect(sessionStorage.length).toBe(10);
 const onError=vi.fn(),blocked={getItem(){throw Error()},get length(){throw Error()}};
 const tracker=createPaperInsights(attempt(),{storage:blocked,onError});tracker.active(5);tracker.finish();expect(onError).toHaveBeenCalledOnce();
});
