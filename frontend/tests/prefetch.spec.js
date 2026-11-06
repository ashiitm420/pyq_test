import {it,expect,vi,afterEach} from 'vitest';
import {schedulePrefetch} from '../src/prefetch';
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();vi.restoreAllMocks()});
it('skips optional work on data saver and slow connections',async()=>{
 vi.useFakeTimers();const work=vi.fn();
 for(const connection of [{saveData:true},{effectiveType:'2g'},{effectiveType:'3g'}]){
  vi.stubGlobal('navigator',{connection});
  schedulePrefetch(work);await vi.runAllTimersAsync();
 }
 expect(work).not.toHaveBeenCalled();
});
it('cancels pending intent work and runs it once when allowed',async()=>{
 vi.useFakeTimers();const work=vi.fn();
 const cancel=schedulePrefetch(work);cancel();await vi.runAllTimersAsync();expect(work).not.toHaveBeenCalled();
 schedulePrefetch(work);await vi.runAllTimersAsync();expect(work).toHaveBeenCalledTimes(1);
});
