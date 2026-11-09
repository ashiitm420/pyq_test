import {it,expect,vi} from 'vitest';import {mount,flushPromises} from '@vue/test-utils';import Records from '../src/Records.vue';
const mocks=vi.hoisted(()=>({api:vi.fn(),session:{},go:vi.fn()}));vi.mock('../src/api',()=>mocks);
it('colours outcomes and jumps to the correct review page',async()=>{
 const palette=['CORRECT','INCORRECT','PARTIAL','SKIPPED'].map((outcome,n)=>({question_id:n+1,number:String(n+1),state:outcome==='SKIPPED'?'NOT_VISITED':'ANSWERED',outcome,review_index:n===3?25:n}));
 mocks.api.mockImplementation(async path=>path==='/attempts/1'?{id:1,status:'SUBMITTED',palette,result:{score:2,total_marks:4,percentage:50}}:{items:[{question:{id:4,number:'4',text:'Fourth',options:[],images:[],answers:['A']},outcome:'SKIPPED',ai_solution:{available:false}}],total:26});
 const scroll=vi.fn();Element.prototype.scrollIntoView=scroll;
 const w=mount(Records,{props:{route:'/result/1'},attachTo:document.body});await flushPromises();
 expect(w.find('.result-correct').exists()).toBe(true);expect(w.find('.result-incorrect').exists()).toBe(true);expect(w.find('.result-partial').exists()).toBe(true);expect(w.find('.result-skipped').exists()).toBe(true);
 await w.get('.result-skipped').trigger('click');await flushPromises();
 expect(mocks.api).toHaveBeenCalledWith('/attempts/1/review?page=26&limit=1');expect(scroll).toHaveBeenCalledWith({behavior:'smooth',block:'start'});
 const count=mocks.api.mock.calls.length;await w.get('.result-skipped').trigger('click');await flushPromises();expect(mocks.api.mock.calls.length).toBe(count);w.unmount();delete Element.prototype.scrollIntoView;
});

it('shows marks, active time, marked and unsure counts together without a metrics API',async()=>{
 const a={id:3,custom_exam:true,status:'SUBMITTED',title:'Custom exam',expires_at:Date.now()/1000+3600,papers:[{id:1,source_paper_id:5,title:'Finance'}],palette:[{question_id:11,paper_id:5,number:'1',state:'ANSWERED_AND_MARKED_FOR_REVIEW',outcome:'CORRECT',marked:true}],result:{score:2,total_marks:4,percentage:50,papers:[{id:1,source_paper_id:5,title:'Finance',score:2,total_marks:4}]}};
 sessionStorage.setItem('pyq-paper-insights-v1-3',JSON.stringify({version:1,expiresAt:Date.now()+3600000,time:{5:3120000},unsure:[11]}));
 mocks.api.mockImplementation(async path=>path==='/attempts/3'?a:{items:[],total:0});
 const w=mount(Records,{props:{route:'/result/3'},global:{stubs:{ShareResult:true,SupportEntry:true}}});await flushPromises();
 const table=w.get('[aria-label="Paper performance summary"]');expect(table.findAll('tbody tr')[0].findAll('th,td').map(c=>c.text())).toEqual(['Finance','2/4','52 min','1','1','Review']);
 expect(mocks.api.mock.calls.every(([path])=>!path.includes('insights'))).toBe(true);w.unmount();sessionStorage.clear();
});
