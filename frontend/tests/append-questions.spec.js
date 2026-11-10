import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
const mocks=vi.hoisted(()=>({api:vi.fn(),invalidateCatalog:vi.fn()}));
vi.mock('../src/api',()=>mocks);
import AppendQuestions from '../src/AppendQuestions.vue';
afterEach(()=>{vi.clearAllMocks();vi.unstubAllGlobals()});
async function fill(w,number){await w.get('[aria-label="Paper question number"]').setValue(number);await w.get('[aria-label="Question text"]').setValue('Question '+number);const opts=w.findAll('[aria-label="Option text"]');await opts[0].setValue('Alpha');await opts[1].setValue('Beta')}
it('queues two questions, previews and appends as hidden drafts in one request',async()=>{
 mocks.api.mockResolvedValue({ids:[10,11],created:2});const w=mount(AppendQuestions,{props:{paperId:7,paperName:'Finance'}});
 await fill(w,'14');await w.findAll('button').find(b=>b.text()==='+ Add another').trigger('click');await fill(w,'15');
 await w.get('form').trigger('submit');await flushPromises();
 expect(mocks.api).toHaveBeenCalledTimes(1);expect(mocks.api).toHaveBeenCalledWith('/admin/papers/7/questions/append',expect.objectContaining({method:'POST',body:expect.objectContaining({publish:false,questions:expect.arrayContaining([expect.objectContaining({number:'14'}),expect.objectContaining({number:'15'})])})}));
 expect(w.text()).toContain('2 questions saved as hidden drafts');expect(w.emitted('saved')).toHaveLength(1);
 await w.findAll('button').find(b=>b.text().includes('Edit question 15')).trigger('click');expect(w.emitted('edit')[0]).toEqual([11]);w.unmount();
});
it('retains the request id for a failed retry and sends publication choice',async()=>{
 mocks.api.mockRejectedValueOnce(Error('Connection lost')).mockResolvedValue({ids:[10],created:0,replayed:true});const w=mount(AppendQuestions,{props:{paperId:7}});await fill(w,'14');await w.get('input[type="checkbox"]').setValue(true);
 await w.get('form').trigger('submit');await flushPromises();expect(w.text()).toContain('Connection lost');const first=mocks.api.mock.calls[0][1].body.request_id;
 await w.get('form').trigger('submit');await flushPromises();expect(mocks.api.mock.calls[1][1].body.request_id).toBe(first);expect(mocks.api.mock.calls[1][1].body.publish).toBe(true);w.unmount();
});
it('rejects duplicate numbers locally before making a request',async()=>{
 const w=mount(AppendQuestions,{props:{paperId:7}});await fill(w,'14');await w.findAll('button').find(b=>b.text()==='+ Add another').trigger('click');await fill(w,'14');await w.get('form').trigger('submit');await flushPromises();expect(w.text()).toContain('Question numbers must be unique');expect(mocks.api).not.toHaveBeenCalled();w.unmount();
});
