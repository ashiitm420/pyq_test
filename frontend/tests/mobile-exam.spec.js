import {it,expect,vi,beforeEach,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import Exam from '../src/Exam.vue';
const mocks=vi.hoisted(()=>({api:vi.fn(),go:vi.fn(),session:{user:{name:'Student'}}}));
vi.mock('../src/api',()=>mocks);
let a,items,media,w;
beforeEach(()=>{
 vi.useFakeTimers();sessionStorage.clear();media={matches:true,addEventListener:vi.fn(),removeEventListener:vi.fn()};vi.stubGlobal('matchMedia',()=>media);
 a={id:1,status:'ACTIVE',mode:'practice',title:'Algorithms · Quiz 1',server_time:Date.now()/1000,deadline:null,palette:[1,2].map(id=>({question_id:id,number:String(id),paper_id:id,state:'NOT_VISITED'}))};
 items=a.palette.map(p=>({question:{id:p.question_id,number:p.number,paper_id:p.paper_id,kind:'NAT',text:'Enter a number',marks:1,options:[],images:[]},answer:null,marked:false}));
 mocks.api.mockReset();mocks.api.mockImplementation(async(path,o)=>{
 if(path.endsWith('?bootstrap=1'))return {...a,items};
 if(path.endsWith('/switch-mode'))return {...a,mode:o.body.mode,deadline:Date.now()/1000+3600};
 if(path.endsWith('/answers'))return {items:o.body.items.map(x=>({question_id:x.question_id,state:x.marked?'MARKED_FOR_REVIEW':'ANSWERED'}))};
 return {items:[]};
 });
});
afterEach(()=>{w?.unmount();w=null;vi.useRealTimers();vi.unstubAllGlobals()});
it('keeps the palette closed, retains and autosaves drafts after next, and confirms Finish',async()=>{
 a.mode='exam';a.deadline=Date.now()/1000+3600;w=mount(Exam,{props:{id:1}});await flushPromises();expect(w.find('.exam-header').exists()).toBe(false);expect(w.find('.palette-panel').exists()).toBe(false);
 await w.get('input.numeric-answer').setValue('3/4');await w.get('.mobile-save-next').trigger('click');await vi.advanceTimersByTimeAsync(900);await flushPromises();
 expect(mocks.api).toHaveBeenCalledWith('/attempts/1/answers',expect.objectContaining({body:{items:expect.arrayContaining([expect.objectContaining({question_id:1,answer:'3/4'})])}}));
 expect(w.get('.mobile-question-position').text()).toBe('Q 2 / 2');await w.get('.mobile-save-next').trigger('click');expect(w.find('[role="dialog"]').exists()).toBe(true);expect(mocks.api.mock.calls.some(([p])=>p.endsWith('/submit'))).toBe(false);
});
it('opens palette on demand and closes it after selection or Escape',async()=>{
 w=mount(Exam,{props:{id:1}});await flushPromises();await w.get('[aria-label="Open question palette"]').trigger('click');expect(w.find('[aria-modal="true"]').exists()).toBe(true);
 await w.findAll('.palette button')[1].trigger('click');await flushPromises();expect(w.find('.palette-panel').exists()).toBe(false);expect(w.get('.mobile-question-position').text()).toBe('Q 2 / 2');
 await w.get('[aria-label="Open question palette"]').trigger('click');window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));await flushPromises();expect(w.find('.palette-panel').exists()).toBe(false);
});
it('retains mark-for-review and tools without showing the desktop toolbar',async()=>{
 w=mount(Exam,{props:{id:1}});await flushPromises();await w.get('.mobile-review').trigger('click');expect(w.get('.mobile-review').attributes('aria-pressed')).toBe('true');
 await w.get('[aria-label="More exam tools"]').trigger('click');expect(w.get('.mobile-exam-tools-sheet').text()).toContain('Calculator');await w.findAll('.mobile-tools-grid button').find(b=>b.text()==='Instructions').trigger('click');expect(w.find('.mobile-exam-tools-sheet').exists()).toBe(false);expect(w.findAll('[role="dialog"]').some(d=>d.text().includes('Exam instructions'))).toBe(true);
});
it('switches mode through the existing endpoint and shows the exam timer',async()=>{
 w=mount(Exam,{props:{id:1}});await flushPromises();await w.findAll('.mobile-mode-switch button')[1].trigger('click');await flushPromises();expect(mocks.api).toHaveBeenCalledWith('/attempts/1/switch-mode',expect.objectContaining({body:{mode:'exam',duration_seconds:5400}}));expect(w.find('.mobile-timer').exists()).toBe(true);
});
it('switches custom papers without another question fetch',async()=>{
 a.custom_exam=true;a.papers=[{id:10,source_paper_id:1,title:'Finance'},{id:20,source_paper_id:2,title:'Industry'}];
 w=mount(Exam,{props:{id:1}});await flushPromises();await w.get('[aria-label="Choose paper"]').setValue('20');await flushPromises();expect(w.get('.mobile-question-position').text()).toBe('Q 2 / 2');expect(mocks.api.mock.calls.filter(([p])=>p.includes('bootstrap'))).toHaveLength(1);
});
