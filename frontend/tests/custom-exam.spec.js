import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import CustomExamBuilder from '../src/CustomExamBuilder.vue';
import Exam from '../src/Exam.vue';
const mocks=vi.hoisted(()=>({api:vi.fn(),go:vi.fn(),session:{user:{id:1,role:'ADMIN'}}}));vi.mock('../src/api',()=>mocks);
afterEach(()=>{vi.restoreAllMocks();vi.clearAllMocks();sessionStorage.clear();mocks.session.user={id:1,role:'ADMIN'}});
it('creates one admin-only combined attempt with chosen papers and one duration',async()=>{
 mocks.api.mockImplementation(async path=>path==='/catalog'?{courses:[],meta:{exams:[]}}:path.startsWith('/papers?')?{items:[{id:1,course:'CF',question_count:10},{id:2,course:'Industry',question_count:20}],total:2}:{id:88});
 vi.spyOn(window,'confirm').mockReturnValue(true);
 const w=mount(CustomExamBuilder);await flushPromises();
 for(const el of w.findAll('input[type=checkbox]'))await el.setValue(true);
 await w.get('input[type=number]').setValue(90);
 await w.findAll('button').find(b=>b.text()==='Start custom exam').trigger('click');await flushPromises();
 expect(mocks.api).toHaveBeenCalledWith('/attempts',{method:'POST',body:{paper_ids:[1,2],mode:'exam',duration_seconds:5400}});expect(mocks.go).toHaveBeenCalledWith('/attempt/88');w.unmount();
});
it('does not load the builder for guests and prevents a fifth paper or excess questions',async()=>{
 mocks.session.user=null;let w=mount(CustomExamBuilder);await flushPromises();expect(mocks.api).not.toHaveBeenCalled();w.unmount();mocks.session.user={role:'ADMIN'};
 mocks.api.mockImplementation(async p=>p==='/catalog'?{courses:[],meta:{}}:{items:Array.from({length:5},(_,i)=>({id:i+1,question_count:10})),total:5});
 w=mount(CustomExamBuilder);await flushPromises();for(const c of w.findAll('input[type=checkbox]').slice(0,4))await c.setValue(true);expect(w.findAll('input[type=checkbox]')[4].attributes('disabled')).toBeDefined();w.unmount();
});
it('switches source papers locally, retains answers, and remembers the previous question',async()=>{
 const papers=[{id:1,source_paper_id:1,title:'Finance',questions:2},{id:2,source_paper_id:2,title:'Industry',questions:1}];
 const palette=[{question_id:11,paper_id:1,number:'1',state:'NOT_VISITED'},{question_id:12,paper_id:1,number:'2',state:'NOT_VISITED'},{question_id:21,paper_id:2,number:'1',state:'NOT_VISITED'}];
 const items=palette.map(p=>({question:{id:p.question_id,paper_id:p.paper_id,number:p.number,text:'Question '+p.question_id,kind:'MCQ',marks:2,negative_marks:0,options:[{key:'A',text:'Answer'}],images:[]},answer:null,visited:false,marked:false}));
 mocks.api.mockResolvedValue({id:88,status:'ACTIVE',mode:'exam',title:'Custom exam',custom_exam:true,papers,palette,items,server_time:Date.now()/1000,deadline:Date.now()/1000+3600});
 const w=mount(Exam,{props:{id:88},global:{stubs:{QuestionContent:true,ComprehensionLayout:{template:'<div><slot/></div>'},SavedAISolution:true,ReportFormat:true}}});await flushPromises();
 expect(w.find('.mode-switch').exists()).toBe(false);
 const tabs=w.get('[aria-label="Exam papers"]');
 await w.get('.option').trigger('click');
 await w.findAll('.palette button')[1].trigger('click');
 await tabs.findAll('button')[1].trigger('click');expect(w.text()).toContain('Industry');
 await tabs.findAll('button')[0].trigger('click');expect(w.get('.current-question-label').text()).toContain('Question 2');
 await w.findAll('.palette button')[0].trigger('click');expect(w.get('.option').attributes('aria-pressed')).toBe('true');
 await w.findAll('button').find(b=>b.text()==='Mark for review').trigger('click');
 await w.findAll('button').find(b=>b.text()==='Submit exam').trigger('click');
 expect(w.get('[aria-labelledby=submit-title]').text()).toContain('1 marked for review');
 expect(mocks.api).toHaveBeenCalledTimes(1);w.unmount();
});
