import {it,expect,vi,beforeEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
import SupportCheckout from '../src/SupportCheckout.vue';
import SupportEntry from '../src/SupportEntry.vue';
import {api} from '../src/api';
import {loadRazorpay} from '../src/razorpayCheckout';
vi.mock('../src/api',()=>({api:vi.fn(),session:{csrf:'test'},loadSession:vi.fn()}));
vi.mock('../src/razorpayCheckout',()=>({loadRazorpay:vi.fn()}));
let options,failed,open;
beforeEach(()=>{
 vi.clearAllMocks();options=null;failed=null;open=vi.fn();
 loadRazorpay.mockResolvedValue(function(o){options=o;return {open,on:(event,fn)=>{failed=fn},close:vi.fn()}});
 api.mockImplementation(async path=>path==='/create-order'?{order_id:'order_test',amount:5000,currency:'INR',key_id:'rzp_test_fake',test_mode:true}:{success:true,paid:true,status:'captured'});
});
it('does not load checkout or contact the server just to display a support button',()=>{
 const w=mount(SupportEntry);expect(w.text()).toContain('Support MauryaHub');
 expect(loadRazorpay).not.toHaveBeenCalled();expect(api).not.toHaveBeenCalled();w.unmount();
});
it('creates an order in paise and verifies all callback fields before thanking the supporter',async()=>{
 const w=mount(SupportCheckout);await w.get('form').trigger('submit');await flushPromises();
 expect(api).toHaveBeenCalledWith('/create-order',{method:'POST',body:{amount:5000,currency:'INR'}});
 expect(open).toHaveBeenCalledTimes(1);expect(options.order_id).toBe('order_test');
 expect(w.text()).not.toContain('Thank you for supporting');
 const fields={razorpay_payment_id:'pay_test',razorpay_order_id:'order_test',razorpay_signature:'signature'};
 await options.handler(fields);await flushPromises();
 expect(api).toHaveBeenLastCalledWith('/verify-payment',{method:'POST',body:fields});
 expect(w.text()).toContain('Your payment has been verified');w.unmount();
});
it('handles cancellation and payment failure without claiming success',async()=>{
 const w=mount(SupportCheckout);await w.get('form').trigger('submit');await flushPromises();
 failed({});await flushPromises();expect(w.get('[role="alert"]').text()).toContain('Payment failed');
 options.modal.ondismiss();await flushPromises();expect(w.text()).toContain('Checkout closed');
 expect(api.mock.calls.filter(c=>c[0]==='/verify-payment')).toHaveLength(0);w.unmount();
});
it('offers status verification retry without creating another charge/order',async()=>{
 const w=mount(SupportCheckout);await w.get('form').trigger('submit');await flushPromises();
 api.mockRejectedValueOnce(Error('Offline'));await options.handler({razorpay_payment_id:'p',razorpay_order_id:'o',razorpay_signature:'s'});await flushPromises();
 expect(w.text()).toContain('do not pay again');
 await w.findAll('button').find(b=>b.text()==='Check payment status').trigger('click');await flushPromises();
 expect(w.text()).toContain('Your payment has been verified');
 expect(api.mock.calls.filter(c=>c[0]==='/create-order')).toHaveLength(1);w.unmount();
});
