import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import AISolutions from '../src/AISolutions.vue';
const mocks=vi.hoisted(()=>({api:vi.fn()}));vi.mock('../src/api',()=>mocks);
afterEach(()=>vi.restoreAllMocks());
it('publishes flagged selections only with explicit review approval',async()=>{
 const row={question_id:17,number:'1',kind:'MCQ',solution:{status:'NEEDS_REVIEW',text:'Explanation',checks:['Check answer']}};
 mocks.api.mockImplementation(async path=>{
  if(path==='/catalog')return {courses:[]};if(path==='/metadata')return {exams:[]};
  if(path==='/papers/1')return {id:1,course_id:2,exam_type_id:3};
  if(path.includes('/summary?'))return {papers:[],statistics:{}};
  if(path==='/admin/ai-solutions/bulk-publish')return {published:[17],skipped:[]};
  return {items:[row],total:1};
 });
 const confirm=vi.spyOn(window,'confirm').mockReturnValue(true);
 const w=mount(AISolutions,{props:{initialPaperId:1},global:{stubs:{ImportPaperSolutions:true,ImportSolutionBundle:true}}});await flushPromises();
 await w.findAll('button').find(b=>b.text()==='Select ready / needs-review on this page').trigger('click');
 await w.findAll('label').find(l=>l.text().includes('I reviewed')).get('input').setValue(true);
 await w.findAll('button').find(b=>b.text()==='Publish selected solutions').trigger('click');await flushPromises();
 expect(confirm).toHaveBeenCalled();expect(mocks.api).toHaveBeenCalledWith('/admin/ai-solutions/bulk-publish',{method:'POST',body:{question_ids:[17],review_confirmed:true}});
 expect(w.text()).toContain('1 published · 0 skipped');w.unmount();
});
