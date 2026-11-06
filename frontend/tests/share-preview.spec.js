import {it,expect,vi} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import ShareResult from '../src/ShareResult.vue';
vi.mock('../src/shareCard',()=>({shareSummary:()=>({}),shareText:()=>'My score',buildShareImage:async()=>new Blob(['png'],{type:'image/png'}),whatsappUrl:()=> 'https://wa.me/?text=My%20score'}));
it('shows a generated preview and releases its object URL',async()=>{
 const originalCreate=URL.createObjectURL,originalRevoke=URL.revokeObjectURL;
 URL.createObjectURL=vi.fn(()=>'blob:result-preview');
 const revoke=URL.revokeObjectURL=vi.fn();
 const w=mount(ShareResult,{props:{attempt:{}}});
 await w.get('button').trigger('click');await flushPromises();
 expect(w.get('img').attributes('src')).toBe('blob:result-preview');
 expect(w.text()).toContain('WhatsApp text');
 w.unmount();expect(revoke).toHaveBeenCalledWith('blob:result-preview');URL.createObjectURL=originalCreate;URL.revokeObjectURL=originalRevoke;
});
