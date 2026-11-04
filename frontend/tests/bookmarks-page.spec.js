import {it,expect,vi,beforeEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
const mocks=vi.hoisted(()=>({api:vi.fn(),go:vi.fn()}));vi.mock('../src/api',()=>mocks);
import BookmarksPage from '../src/BookmarksPage.vue';
import {setBookmark,bookmarkRows} from '../src/browserStore';
const q=(id,paper,title,text,saved,extra={})=>({id,paper_id:paper,number:String(id),kind:'MCQ',marks:2,text,options:[{key:'k1',text:'Alpha'},{key:'k2',text:'Beta'}],images:[],...extra,_saved:saved,_title:title});
beforeEach(()=>{localStorage.clear();vi.useRealTimers();mocks.api.mockReset();mocks.go.mockReset();
 let t=1000;for(const b of [q(1,5,'Economics · Quiz 1 · May 2026','Real interest rate?',1),q(2,5,'Economics · Quiz 1 · May 2026','Bond duration?',2),q(3,9,'Statistics I · Quiz 2 · Jan 2026','Find the median',3),q(4,11,'','Untitled old bookmark',4)]){vi.spyOn(Date,'now').mockReturnValue(t+=1000);setBookmark(b,true,{paper_title:b._title})}
 vi.restoreAllMocks()});

it('groups by paper, shows Q number and marks, hides empty topic, and reveals options with letters',async()=>{
 const w=mount(BookmarksPage);await flushPromises();
 expect(w.text()).toContain('4 questions saved');
 const heads=w.findAll('.bm-group-head h2').map(h=>h.text());
 expect(heads).toEqual(['Paper #11','Statistics I · Quiz 2 · Jan 2026','Economics · Quiz 1 · May 2026']);
 expect(w.text()).not.toContain('Topic not specified');
 expect(w.find('.bm-meta').text()).toContain('Q4');expect(w.find('.bm-meta').text()).toContain('2 marks');
 await w.findAll('button').find(b=>b.text().startsWith('Show options')).trigger('click');
 expect(w.find('.bm-options').text()).toContain('A.');expect(w.find('.bm-options').text()).toContain('Alpha');
 expect(w.find('a[href="/study/papers/11#question-4"]').exists()).toBe(true);
});

it('filters by search and course and sorts oldest first',async()=>{
 const w=mount(BookmarksPage);await flushPromises();
 await w.get('input[type=search]').setValue('bond');expect(w.findAll('.bm-card')).toHaveLength(1);expect(w.text()).toContain('Bond duration?');
 await w.get('input[type=search]').setValue('beta');expect(w.findAll('.bm-card')).toHaveLength(4);
 await w.get('input[type=search]').setValue('');await w.get('select[aria-label="Filter by course"]').setValue('Statistics I');expect(w.findAll('.bm-card')).toHaveLength(1);
 await w.get('select[aria-label="Filter by course"]').setValue('');await w.get('select[aria-label="Sort bookmarks"]').setValue('oldest');
 expect(w.findAll('.bm-group-head h2')[0].text()).toBe('Economics · Quiz 1 · May 2026');
});

it('removes with undo and practises one paper group',async()=>{
 mocks.api.mockResolvedValue({id:77});
 const w=mount(BookmarksPage);await flushPromises();
 await w.findAll('.bm-remove')[0].trigger('click');expect(bookmarkRows()).toHaveLength(3);expect(w.find('.bm-toast').text()).toContain('Bookmark removed');
 await w.get('.bm-toast button').trigger('click');expect(bookmarkRows()).toHaveLength(4);expect(w.find('.bm-toast').exists()).toBe(false);
 await w.findAll('button').find(b=>b.text()==='Practice 2').trigger('click');await flushPromises();
 expect(mocks.api).toHaveBeenCalledWith('/attempts',{method:'POST',body:{collection:'bookmarks',mode:'practice',question_ids:expect.arrayContaining([1,2])}});
 expect(mocks.api.mock.calls[0][1].body.question_ids).toHaveLength(2);expect(mocks.go).toHaveBeenCalledWith('/attempt/77');
});

it('shows the answer and solution on demand, loading one paper once',async()=>{
 mocks.api.mockImplementation(async path=>path.startsWith('/papers/5/answers')?{items:[{id:1,answers:['k2'],answer_status:'ANSWER_AVAILABLE',explanation:null,solution:'Use the Fisher equation.'},{id:2,answers:[],answer_status:'NOT_AVAILABLE',explanation:null,solution:null}]}:{items:[]});
 const w=mount(BookmarksPage);await flushPromises();
 const card=text=>w.findAll('.bm-card').find(c=>c.text().includes(text));
 expect(w.find('.bm-answer').exists()).toBe(false);expect(mocks.api).not.toHaveBeenCalled();
 await card('Real interest rate?').findAll('button').find(b=>b.text()==='Show answer').trigger('click');await flushPromises();
 expect(mocks.api).toHaveBeenCalledTimes(1);
 const [path]=mocks.api.mock.calls[0];expect(path.split('?')[0]).toBe('/papers/5/answers');expect(new URLSearchParams(path.split('?')[1]).get('ids').split(',').sort()).toEqual(['1','2']);
 const first=card('Real interest rate?');
 expect(first.get('.bm-answer').text()).toContain('Option B');expect(first.get('.bm-answer').text()).toContain('Use the Fisher equation.');
 expect(first.find('.bm-correct').text()).toContain('Beta');expect(first.findAll('.bm-correct')).toHaveLength(1);
 await card('Bond duration?').findAll('button').find(b=>b.text()==='Show answer').trigger('click');await flushPromises();
 expect(mocks.api).toHaveBeenCalledTimes(1);
 expect(card('Bond duration?').get('.bm-answer').text()).toContain('Answer key not available');
 await first.findAll('button').find(b=>b.text()==='Hide answer').trigger('click');
 expect(card('Real interest rate?').find('.bm-answer').exists()).toBe(false);
});

it('offers retry when the answer cannot load',async()=>{
 mocks.api.mockRejectedValueOnce(new Error('Network down')).mockResolvedValue({items:[{id:3,answers:['k1'],answer_status:'ANSWER_AVAILABLE'}]});
 const w=mount(BookmarksPage);await flushPromises();
 const card=()=>w.findAll('.bm-card').find(c=>c.text().includes('Find the median'));
 await card().findAll('button').find(b=>b.text()==='Show answer').trigger('click');await flushPromises();
 expect(card().get('.bm-answer').text()).toContain('Network down');
 await card().get('.bm-answer .text-btn').trigger('click');await flushPromises();
 expect(card().get('.bm-answer').text()).toContain('Option A');
});
