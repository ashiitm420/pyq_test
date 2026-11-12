import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
const mocks=vi.hoisted(()=>({api:vi.fn(),invalidateCatalog:vi.fn()}));vi.mock('../src/api',()=>mocks);
import Editor from '../src/PaperQuestionEditor.vue';
const rows=()=>[1,2].map(id=>({updated_at:id,status:'AVAILABLE',question:{id,number:String(id),kind:'MCQ',text:'Question '+id,options:[{key:'A',text:'Alpha'},{key:'B',text:'Beta'}],answers:['A'],marks:2,negative_marks:0,tolerance:0,images:[]}}));
afterEach(()=>{vi.clearAllMocks();vi.unstubAllGlobals()});
it('loads once, retains drafts across questions and submits only changed rows',async()=>{
 mocks.api.mockResolvedValueOnce({items:rows()}).mockResolvedValueOnce({saved:[{id:1,updated_at:20}]});
 const w=mount(Editor,{props:{paperId:7}});await flushPromises();
 await w.get('[aria-label="Question text"]').setValue('Corrected first');
 await w.findAll('button').find(b=>b.text()==='Next question').trigger('click');
 expect(w.get('[aria-label="Question text"]').element.value).toBe('Question 2');
 await w.findAll('button').find(b=>b.text()==='Previous question').trigger('click');
 expect(w.get('[aria-label="Question text"]').element.value).toBe('Corrected first');
 await w.get('form').trigger('submit');await flushPromises();
 const req=mocks.api.mock.calls[1];expect(req[0]).toBe('/admin/papers/7/questions/edit');expect(req[1].body.questions).toHaveLength(1);
 expect(req[1].body.questions[0]).toMatchObject({id:1,updated_at:1,text:'Corrected first',answers:['A']});
 expect(w.text()).toContain('1 questions updated together');expect(w.text()).toContain('Save all changes (0)');w.unmount();
});
it('keeps unsaved work on conflict and blocks invalid answer JSON locally',async()=>{
 mocks.api.mockResolvedValueOnce({items:rows()}).mockRejectedValueOnce(Error('Question changed; reopen editor'));
 const w=mount(Editor,{props:{paperId:7}});await flushPromises();
 await w.get('[aria-label="Correct answer"]').setValue('bad json');await w.get('form').trigger('submit');await flushPromises();expect(mocks.api).toHaveBeenCalledTimes(1);expect(w.text()).toContain('invalid answer JSON');
 await w.get('[aria-label="Correct answer"]').setValue('["B"]');await w.get('form').trigger('submit');await flushPromises();
 expect(w.text()).toContain('reopen editor');expect(w.get('[aria-label="Correct answer"]').element.value).toBe('["B"]');w.unmount();
});
