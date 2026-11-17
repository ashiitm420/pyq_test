import {it,expect,vi,afterEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import Admin from '../src/Admin.vue';
const m=vi.hoisted(()=>({api:vi.fn(),loadCatalog:vi.fn(),invalidateCatalog:vi.fn(),session:{user:{role:'ADMIN'}}}));vi.mock('../src/api',()=>m);
let w;afterEach(()=>{w?.unmount();vi.restoreAllMocks();localStorage.clear()});
async function setup(run){
 m.api.mockClear();localStorage.setItem('pyq-admin-tab','Catalog Sync');m.loadCatalog.mockResolvedValue({courses:[],meta:{terms:[],exams:[]}});
 m.api.mockImplementation(async p=>p.endsWith('/run-next')?run():null);w=mount(Admin);await flushPromises();w.vm.syncBatch={id:1,done:false,completed:0,failed:0,queued:2,active:0};
}
it('keeps the sequential batch running while the browser tab is hidden',async()=>{
 vi.spyOn(document,'hidden','get').mockReturnValue(true);let calls=0;
 await setup(()=>({id:1,completed:++calls,failed:0,active:0,queued:2-calls,done:calls===2}));await w.vm.runWebBatch();
 expect(calls).toBe(2);expect(w.vm.webRunnerActive).toBe(false);expect(w.text()).not.toContain('Processing paused while this tab is hidden');
});
it('still honours manual pause after the current paper',async()=>{
 let finish;await setup(()=>new Promise(resolve=>{finish=resolve}));const run=w.vm.runWebBatch();await flushPromises();w.vm.pauseWebBatch();finish({id:1,done:false,completed:1,failed:0,queued:1,active:0});await run;
 expect(m.api.mock.calls.filter(([p])=>p.endsWith('/run-next'))).toHaveLength(1);
});
it('still stops after three consecutive failures in a hidden tab',async()=>{
 vi.spyOn(document,'hidden','get').mockReturnValue(true);let failed=0;await setup(()=>({id:1,done:false,completed:0,failed:++failed,queued:10,active:0}));await w.vm.runWebBatch();expect(failed).toBe(3);expect(w.text()).toContain('3 consecutive failures');
});
