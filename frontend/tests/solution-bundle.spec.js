import {it,expect,vi,beforeEach} from 'vitest';import {webcrypto} from 'node:crypto';import {mount,flushPromises} from '@vue/test-utils';import ImportSolutionBundle from '../src/ImportSolutionBundle.vue';
const mock=vi.hoisted(()=>({api:vi.fn()}));vi.mock('../src/api',()=>mock);
const bundle=(ids=[1,2])=>JSON.stringify({format:'pyq-solutions-bundle-v1',papers:ids.map(id=>({format:'pyq-solutions-v1',paper_id:id,solutions:[{question_id:id}]}))});
const result=id=>({paper_id:id,paper_name:'Paper',missing:0,items:[{question_id:id,number:'1',text:'Explanation',status:'CHECKS_PASSED',checks:[]}],published:1,saved:1,needs_review:0});
const button=(w,label)=>w.findAll('button').find(b=>b.text().includes(label));
async function settle(){for(let i=0;i<8;i++){await new Promise(r=>setTimeout(r,5));await flushPromises()}}
beforeEach(()=>{localStorage.clear();mock.api.mockReset();vi.stubGlobal('crypto',webcrypto);mock.api.mockImplementation(async(path,args)=>({papers:[result(args.body.bundle.papers[0].paper_id)]}))});
it('supports 50 selections and sends sequential single-paper preview and save requests',async()=>{
 const w=mount(ImportSolutionBundle,{props:{paperIds:Array.from({length:50},(_,i)=>i+1)}});expect(w.text()).toContain('50 / 50');
 await w.get('textarea').setValue(bundle());await button(w,'Preview bundle').trigger('click');await settle();expect(mock.api).toHaveBeenCalledTimes(2);
 await button(w,'Save & Publish').trigger('click');await settle();const writes=mock.api.mock.calls.filter(c=>c[1].body.save);expect(writes.map(c=>c[1].body.bundle.papers[0].paper_id)).toEqual([1,2]);expect(writes.every(c=>c[1].body.skip_identical)).toBe(true);expect(w.text()).toContain('2 / 2 papers saved');w.unmount();
});
it('continues after a failure and retries only the failed paper',async()=>{
 let fail=true;mock.api.mockImplementation(async(path,args)=>{const id=args.body.bundle.papers[0].paper_id;if(args.body.save&&id===1&&fail)throw Error('Network interrupted');return {papers:[result(id)]}});
 const w=mount(ImportSolutionBundle);await w.get('textarea').setValue(bundle());await button(w,'Preview bundle').trigger('click');await settle();await button(w,'Save & Publish').trigger('click');await settle();expect(w.text()).toContain('1 / 2 papers saved');
 fail=false;mock.api.mockClear();await button(w,'Retry failed').trigger('click');await settle();expect(mock.api).toHaveBeenCalledTimes(1);expect(mock.api.mock.calls[0][1].body.bundle.papers[0].paper_id).toBe(1);expect(w.text()).toContain('2 / 2 papers saved');w.unmount();
});
it('restores progress after reload and skips papers confirmed saved in the database',async()=>{
 let saved=false;mock.api.mockImplementation(async(path,args)=>{const r=result(1);if(args.body.save)saved=true;r.items[0].already_saved=saved;return {papers:[r]}});
 let w=mount(ImportSolutionBundle);await w.get('textarea').setValue(bundle([1]));await button(w,'Preview bundle').trigger('click');await settle();await button(w,'Save & Publish').trigger('click');await settle();w.unmount();
 w=mount(ImportSolutionBundle);await w.get('textarea').setValue(bundle([1]));await button(w,'Preview bundle').trigger('click');await settle();expect(w.text()).toContain('1 / 1 papers saved');mock.api.mockClear();await button(w,'Resume remaining').trigger('click');await settle();expect(mock.api).not.toHaveBeenCalled();w.unmount();
});
it('rejects over-limit and duplicate paper IDs without contacting the server',async()=>{
 const w=mount(ImportSolutionBundle);for(const ids of [[1,1],Array.from({length:51},(_,i)=>i)]){await w.get('textarea').setValue(bundle(ids));await button(w,'Preview bundle').trigger('click');await settle()}expect(mock.api).not.toHaveBeenCalled();w.unmount();
});
it('pauses after the active paper, then resumes without repeating it',async()=>{
 let release;mock.api.mockImplementation(async(path,args)=>{const id=args.body.bundle.papers[0].paper_id;if(args.body.save&&id===1)await new Promise(r=>{release=r});return {papers:[result(id)]}});
 const w=mount(ImportSolutionBundle);await w.get('textarea').setValue(bundle());await button(w,'Preview bundle').trigger('click');await settle();await button(w,'Save & Publish').trigger('click');await settle();
 await button(w,'Pause after').trigger('click');release();await settle();expect(w.text()).toContain('1 / 2 papers saved');expect(mock.api.mock.calls.filter(c=>c[1].body.save)).toHaveLength(1);
 await button(w,'Resume remaining').trigger('click');await settle();expect(w.text()).toContain('2 / 2 papers saved');w.unmount();
});
