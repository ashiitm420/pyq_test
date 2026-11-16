import {it,expect,vi,beforeEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import PostAttemptPrompt from '../src/PostAttemptPrompt.vue';
import QuizRecap from '../src/QuizRecap.vue';
import {promptFor,rememberPrompt,savePreference,markFeedbackSubmitted} from '../src/engagement';
import {api} from '../src/api';
vi.mock('../src/api',()=>({api:vi.fn()}));
const a={id:5,status:'SUBMITTED',mode:'exam'};
beforeEach(()=>{localStorage.clear();vi.clearAllMocks();api.mockResolvedValue({submitted:false})});
it('shows feedback only after a submitted exam, once per attempt and pauses after skipping',()=>{
 expect(promptFor({...a,status:'ACTIVE'})).toBeNull();expect(promptFor({...a,mode:'practice'})).toBeNull();expect(promptFor({...a,custom_exam:true})).toBeNull();
 expect(promptFor(a)).toBe('feedback');rememberPrompt(a.id,'feedback');expect(promptFor(a)).toBeNull();
 savePreference('feedback-skip',Date.now());expect(promptFor({...a,id:6})).toBeNull();
});
it('never asks a known feedback author again and limits support to once per week',()=>{
 markFeedbackSubmitted();expect(promptFor(a)).toBe('support');rememberPrompt(a.id,'support');
 expect(promptFor({...a,id:6})).toBeNull();expect(promptFor({...a,id:7},Date.now()+8*86400000)).toBe('support');
});
it('reconciles server receipts before offering feedback and does not auto-open payment',async()=>{
 api.mockResolvedValue({submitted:true});const w=mount(PostAttemptPrompt,{props:{attempt:a}});await flushPromises();
 expect(w.text()).not.toContain('Give Feedback');expect(w.text()).toContain('Support MauryaHub');
 expect(api).toHaveBeenCalledTimes(1);expect(api).toHaveBeenCalledWith('/feedback/state');w.unmount();
});
it('gives feedback or skips without blocking results, and does not prompt on state errors',async()=>{
 const w=mount(PostAttemptPrompt,{props:{attempt:a}});await flushPromises();
 expect(w.get('[role="dialog"]').exists()).toBe(true);
 await w.findAll('button').find(b=>b.text()==='Give Feedback').trigger('click');
 expect(w.emitted('feedback')).toHaveLength(1);expect(w.find('[role="dialog"]').exists()).toBe(false);w.unmount();
 localStorage.clear();api.mockRejectedValue(Error('Offline'));const other=mount(PostAttemptPrompt,{props:{attempt:a}});await flushPromises();expect(other.find('[role="dialog"]').exists()).toBe(false);other.unmount();
});
it('renders real snapshot numbers and no live request',()=>{
 const w=mount(QuizRecap);expect(w.text()).toContain('2,300');expect(w.text()).toContain('500');expect(w.text()).toContain('200');expect(w.text()).toContain('Reach estimated from participating browsers');expect(w.text()).not.toContain('QUIZ 1');expect(api).not.toHaveBeenCalled();w.unmount();
});
