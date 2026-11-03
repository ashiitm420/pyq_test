import {describe,it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import {shareSummary,shareText,headline,wrapLines,whatsappUrl} from '../src/shareCard';

const attempt={id:7,paper_id:42,title:'Statistics I · Quiz 1 · May 2026 · paper.pdf · timed practice (user-selected duration)',
 palette:Array.from({length:25},(_,n)=>({question_id:n})),
 result:{score:18.5,total_marks:25,percentage:74,accuracy:80.43,correct:17,incorrect:3,partial:1,attempted:21,time_taken:3725,pending_manual:false}};

describe('share card data',()=>{
 it('summarises the score without private details and links to the paper',()=>{
  const s=shareSummary(attempt,'https://www.mauryahub.in');
  expect(s.title).toBe('Statistics I · Quiz 1 · May 2026');
  expect(headline(s)).toBe('74%');
  expect(s.time).toBe('1h 2m');
  expect(s.link).toBe('https://www.mauryahub.in/paper/42');
  expect(s.host).toBe('mauryahub.in');
  const text=shareText(s);
  expect(text).toContain('I scored 74% (18.5/25 marks) in Statistics I · Quiz 1 · May 2026');
  expect(text).toContain('https://www.mauryahub.in/paper/42');
  expect(text).not.toContain('/attempt');expect(text).not.toContain('/result');
 });
 it('falls back when percentage or marks are unknown and marks provisional scores',()=>{
  const s=shareSummary({...attempt,paper_id:null,result:{...attempt.result,percentage:null,total_marks:null,pending_manual:true}},'https://x.in');
  expect(headline(s)).toBe('17/25');
  expect(shareText(s)).toContain('17 correct out of 25 (provisional)');
  expect(s.link).toBe('https://x.in/');
  expect(shareSummary({id:1})).toBeNull();
 });
 it('wraps long titles to at most three lines with an ellipsis',()=>{
  const lines=wrapLines('one two three four five six seven eight nine ten',10,t=>t.length,3);
  expect(lines).toHaveLength(3);expect(lines.every(l=>l.length<=10)).toBe(true);expect(lines[2].endsWith('…')).toBe(true);
 });
 it('encodes the WhatsApp message',()=>{
  expect(whatsappUrl('a & b\nc')).toBe('https://wa.me/?text=a%20%26%20b%0Ac');
 });
});

vi.mock('../src/shareCard',async original=>({...await original(),buildShareImage:vi.fn(async()=>new Blob(['png'],{type:'image/png'}))}));

describe('ShareResult component',()=>{
 afterEach(()=>{delete navigator.canShare;delete navigator.share;vi.restoreAllMocks()});
 it('creates the image only on click and shares the file natively when supported',async()=>{
  const {buildShareImage}=await import('../src/shareCard');buildShareImage.mockClear();
  URL.createObjectURL=vi.fn(()=>'blob:card');URL.revokeObjectURL=vi.fn();
  navigator.canShare=vi.fn(()=>true);navigator.share=vi.fn(async()=>{});
  const ShareResult=(await import('../src/ShareResult.vue')).default;
  const w=mount(ShareResult,{props:{attempt},attachTo:document.body});
  expect(buildShareImage).not.toHaveBeenCalled();
  await w.get('.share-result-btn').trigger('click');await flushPromises();
  expect(buildShareImage).toHaveBeenCalledTimes(1);
  expect(w.get('.share-preview').attributes('src')).toBe('blob:card');
  await w.findAll('button').find(b=>b.text()==='Share image').trigger('click');await flushPromises();
  const arg=navigator.share.mock.calls[0][0];
  expect(arg.files[0].name).toBe('mauryahub-result.png');expect(arg.text).toContain('74%');
  // Reopening reuses the same image.
  await w.get('[aria-label="Close"]').trigger('click');await w.get('.share-result-btn').trigger('click');await flushPromises();
  expect(buildShareImage).toHaveBeenCalledTimes(1);
  w.unmount();expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:card');
 });
 it('offers WhatsApp and download when file sharing is unavailable',async()=>{
  URL.createObjectURL=vi.fn(()=>'blob:card');URL.revokeObjectURL=vi.fn();
  const opened=vi.spyOn(window,'open').mockImplementation(()=>null);
  const ShareResult=(await import('../src/ShareResult.vue')).default;
  const w=mount(ShareResult,{props:{attempt},attachTo:document.body});
  await w.get('.share-result-btn').trigger('click');await flushPromises();
  expect(w.findAll('button').some(b=>b.text()==='Share image')).toBe(false);
  await w.findAll('button').find(b=>b.text()==='WhatsApp').trigger('click');
  expect(opened.mock.calls[0][0]).toMatch(/^https:\/\/wa\.me\/\?text=I%20scored%2074%25/);
  w.unmount();
 });
});
