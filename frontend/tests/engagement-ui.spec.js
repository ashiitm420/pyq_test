import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import Records from '../src/Records.vue';
const mocks=vi.hoisted(()=>({api:vi.fn(),session:{},go:vi.fn()}));vi.mock('../src/api',()=>mocks);
afterEach(()=>{localStorage.clear();vi.clearAllMocks();delete Element.prototype.scrollIntoView});
it('keeps review hearts compact and toggles the fill and count',async()=>{
 mocks.api.mockImplementation(async(path,o)=>path==='/feedback'?{items:[{id:1,name:'Student',stars:5,message:'Helpful',created_at:1,likes:0}],total:1}:path==='/feedback/state'?{submitted:false,liked_ids:[]}:{liked:o.method==='PUT',likes:o.method==='PUT'?1:0});
 const w=mount(Records,{props:{route:'/feedback'}});await flushPromises();
 const b=w.get('.feedback-heart');expect(b.classes()).not.toContain('btn');expect(b.get('svg').attributes('fill')).toBe('none');
 await b.trigger('click');await flushPromises();expect(b.attributes('aria-pressed')).toBe('true');expect(b.get('svg').attributes('fill')).toBe('currentColor');expect(b.text()).toBe('1');
 await b.trigger('click');await flushPromises();expect(b.attributes('aria-pressed')).toBe('false');expect(b.text()).toBe('0');w.unmount();
});
it('always offers Give Feedback on practice results, even when no popup is eligible',async()=>{
 mocks.api.mockResolvedValue({id:3,status:'SUBMITTED',mode:'practice',title:'Practice',expires_at:1,palette:[],result:{score:0,total_marks:1,percentage:0}});
 const scroll=vi.fn();Element.prototype.scrollIntoView=scroll;
 const w=mount(Records,{props:{route:'/result/3'},attachTo:document.body,global:{stubs:{ShareResult:true,SupportEntry:true,SupportButton:true}}});await flushPromises();
 const b=w.get('.result-heading .btn-primary');expect(b.text()).toBe('Give Feedback');await b.trigger('click');await flushPromises();
 expect(scroll).toHaveBeenCalledWith({behavior:'smooth',block:'start'});expect(document.activeElement).toBe(w.get('#result-feedback-section input').element);w.unmount();
});
it('ranks reviews by likes and reorders immediately on like and unlike',async()=>{
 const rows=[{id:1,name:'Old',likes:1},{id:3,name:'Newest',likes:0},{id:2,name:'Middle',likes:1}].map(r=>({...r,stars:5,message:'Helpful',created_at:r.id}));
 mocks.api.mockImplementation(async(p,o)=>p==='/feedback'?{items:rows,total:3}:p==='/feedback/state'?{submitted:false,liked_ids:[]}:{liked:o.method==='PUT',likes:o.method==='PUT'?2:0});
 const w=mount(Records,{props:{route:'/feedback'}});await flushPromises();
 const names=()=>w.findAll('.feedback-author strong').map(b=>b.text());expect(names()).toEqual(['Middle','Old','Newest']);
 await w.get('[aria-label="Like review by Newest"]').trigger('click');await flushPromises();expect(names()).toEqual(['Newest','Middle','Old']);
 await w.get('[aria-label="Unlike review by Newest"]').trigger('click');await flushPromises();expect(names()).toEqual(['Middle','Old','Newest']);w.unmount();
});
