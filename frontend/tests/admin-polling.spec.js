import {it,expect,vi,afterEach} from 'vitest';
import {createAdminPoller} from '../src/adminPolling';
afterEach(()=>vi.useRealTimers());
function setup(refresh=vi.fn(async()=>{})){
 vi.useFakeTimers();const doc=new EventTarget();doc.hidden=false;let active=true;
 const onError=vi.fn(),poll=createAdminPoller({refresh,doc,onError,shouldPoll:()=>active});poll.start();
 return {doc,refresh,poll,onError,idle:()=>{active=false},active:()=>{active=true}};
}
it('makes no requests while idle and detects newly queued work',async()=>{
 const s=setup();s.idle();await vi.advanceTimersByTimeAsync(60000);expect(s.refresh).not.toHaveBeenCalled();s.active();await vi.advanceTimersByTimeAsync(15000);expect(s.refresh).toHaveBeenCalledTimes(1);s.poll.stop();
});
it('pauses hidden tabs and waits before resuming',async()=>{
 const s=setup();s.doc.hidden=true;s.doc.dispatchEvent(new Event('visibilitychange'));await vi.advanceTimersByTimeAsync(60000);expect(s.refresh).not.toHaveBeenCalled();s.doc.hidden=false;s.doc.dispatchEvent(new Event('visibilitychange'));await vi.advanceTimersByTimeAsync(15000);expect(s.refresh).toHaveBeenCalledTimes(1);s.poll.stop();
});
it('never overlaps slow requests or reschedules after unmount',async()=>{
 let resolve;const s=setup(vi.fn(()=>new Promise(r=>{resolve=r})));await vi.advanceTimersByTimeAsync(15000);await vi.advanceTimersByTimeAsync(60000);expect(s.refresh).toHaveBeenCalledTimes(1);s.poll.stop();resolve();await vi.advanceTimersByTimeAsync(60000);expect(s.refresh).toHaveBeenCalledTimes(1);
});
it('backs off errors and resets delay on success',async()=>{
 const s=setup(vi.fn().mockRejectedValueOnce(Error('offline')).mockResolvedValue(undefined));await vi.advanceTimersByTimeAsync(15000);expect(s.onError).toHaveBeenCalledTimes(1);await vi.advanceTimersByTimeAsync(29999);expect(s.refresh).toHaveBeenCalledTimes(1);await vi.advanceTimersByTimeAsync(1);expect(s.refresh).toHaveBeenCalledTimes(2);await vi.advanceTimersByTimeAsync(15000);expect(s.refresh).toHaveBeenCalledTimes(3);s.poll.stop();
});
