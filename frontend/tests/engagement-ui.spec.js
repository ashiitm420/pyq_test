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
