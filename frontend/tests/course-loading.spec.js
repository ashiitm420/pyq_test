import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import Catalog from '../src/Catalog.vue';
import {api} from '../src/api';
vi.mock('../src/api',()=>({api:vi.fn(),loadHome:vi.fn(),session:{},go:vi.fn()}));
afterEach(()=>vi.clearAllMocks());
it('shows papers while optional topics are still pending and tolerates topic failure',async()=>{
 let failTopics;
 api.mockImplementation(path=>{
  if(path.endsWith('/topics'))return new Promise((_,reject)=>{failTopics=reject});
  if(path.startsWith('/papers?'))return Promise.resolve({items:[{id:7,name:'Visible paper',course_id:1,practice_available:true}],total:1});
  if(path==='/metadata')return Promise.resolve({terms:[]});
  return Promise.resolve({id:1,name:'Course',exams:{},paper_count:1});
 });
 const w=mount(Catalog,{props:{route:'/course/1'}});await flushPromises();
 expect(w.text()).toContain('Visible paper');expect(w.find('.request-feedback').exists()).toBe(false);
 failTopics(Error('Optional topics unavailable'));await flushPromises();
 expect(w.find('[role="alert"]').exists()).toBe(false);w.unmount();
});
