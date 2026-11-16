<script setup>
import {ref,computed,onMounted,onUnmounted} from 'vue';
import {api,session,loadSession} from './api';
import {loadRazorpay} from './razorpayCheckout';
const emit=defineEmits(['close']);
const amount=ref('50'),phase=ref('idle'),error=ref(''),message=ref(''),paid=ref(false),testMode=ref(false),root=ref();
const busy=computed(()=>phase.value!=='idle');let checkout=null,verification=null,stopped=false,previous;
async function verify(){
 if(!verification)return;phase.value='verifying';error.value='';
 try{
  const d=await api('/verify-payment',{method:'POST',body:verification});if(stopped)return;
  if(!d.success)throw Error('Payment could not be verified.');
  paid.value=d.paid===true;
  message.value=paid.value?'Thank you for supporting MauryaHub! Your payment has been verified.':'Your payment is authorized and awaiting capture. Please check its status again shortly.';
 }catch(e){if(!stopped)error.value='Verification pending: '+e.message+' Please check status; do not pay again.'}
 finally{if(!stopped)phase.value='idle'}
}
async function pay(){
 if(busy.value||verification)return;error.value='';message.value='';
 if(!/^\d+(?:\.\d{1,2})?$/.test(String(amount.value))||Number(amount.value)<1||Number(amount.value)>10000){error.value='Choose an amount from ₹1 to ₹10,000, with at most two decimal places.';return}
 phase.value='preparing';
 try{
  if(!session.csrf)await loadSession();
  const Razorpay=await loadRazorpay();if(stopped)return;
  const order=await api('/create-order',{method:'POST',body:{amount:Math.round(Number(amount.value)*100),currency:'INR'}});if(stopped)return;
  testMode.value=order.test_mode;phase.value='checkout';
  checkout=new Razorpay({key:order.key_id,amount:order.amount,currency:order.currency,order_id:order.order_id,
   name:'MauryaHub',description:'Optional support for hosting and maintenance',theme:{color:'#285fd8'},
   hidden:{contact:true,email:true},
   handler:async response=>{if(stopped)return;verification={razorpay_payment_id:response.razorpay_payment_id,razorpay_order_id:response.razorpay_order_id,razorpay_signature:response.razorpay_signature};await verify()},
   modal:{ondismiss:()=>{if(!stopped&&phase.value==='checkout'){phase.value='idle';message.value='Checkout closed. You can continue using MauryaHub for free.'}}},
  });
  checkout.on('payment.failed',()=>{if(!stopped)error.value='Payment failed. Try another method in checkout, or close it and retry. If your account was debited, check with the payment provider before paying again.'});
  checkout.open();
 }catch(e){if(!stopped){error.value=e.message;phase.value='idle'}}
}
function close(){if(!busy.value)emit('close')}
function keyboard(e){
 if(e.key==='Escape'){e.stopPropagation();close()}
 if(e.key==='Tab'){
  const controls=[...root.value.querySelectorAll('button,input,a[href]')].filter(n=>!n.matches(':disabled'));
  const first=controls[0],last=controls.at(-1);
  if(!first){e.preventDefault();return}
  if(e.shiftKey&&(document.activeElement===first||document.activeElement===root.value)){e.preventDefault();last.focus()}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
 }
}
onMounted(()=>{previous=document.activeElement;root.value?.focus()});
onUnmounted(()=>{stopped=true;checkout?.close?.();previous?.focus?.()});
</script>
<template><div class="support-overlay"><section ref="root" class="support-dialog panel" role="dialog" aria-modal="true" aria-labelledby="support-title" tabindex="-1" @keydown="keyboard"><div class="section-row"><h2 id="support-title">Support MauryaHub ☕</h2><button type="button" class="btn btn-light" aria-label="Close support" :disabled="busy" @click="close">×</button></div><p>Completely optional. All PYQ practice remains free.</p><p v-if="testMode" class="alert alert-info" role="status">Test mode — no real money is charged.</p><form v-if="!verification" @submit.prevent="pay"><fieldset :disabled="busy"><div class="d-flex gap-2 mb-3"><button v-for="n in [20,50,100]" :key="n" type="button" class="btn btn-light" @click="amount=String(n)">₹{{n}}</button></div><label>Support amount (₹)<input v-model="amount" class="form-control" type="number" min="1" max="10000" step="0.01" required></label><p class="muted small">One-time contribution. Payment details are collected by Razorpay.</p><button type="submit" class="btn btn-primary">{{busy?'Preparing payment…':'Continue to payment'}}</button></fieldset></form><p v-if="phase==='verifying'" role="status">Verifying payment…</p><p v-if="error" class="alert alert-danger mt-3" role="alert">{{error}}</p><p v-if="message" class="alert mt-3" :class="paid?'alert-success':'alert-info'" role="status">{{message}}</p><button v-if="verification&&!paid" class="btn btn-outline-primary" type="button" :disabled="busy" @click="verify">Check payment status</button></section></div></template>
<style scoped>
.support-overlay{position:fixed;inset:0;z-index:1600;display:grid;place-items:center;background:#0008;padding:16px}
.support-dialog{--support-bg:#fff;--support-text:#172943;--support-muted:#576b86;--support-field:#fff;--support-soft:#f1f5f9;--support-border:#cbd5e1;width:min(100%,480px);max-height:90dvh;overflow:auto;background:var(--support-bg)!important;color:var(--support-text)!important;border-color:var(--support-border)!important;color-scheme:light}
:global([data-theme="dark"]) .support-dialog{--support-bg:#1e2938;--support-text:#edf3fc;--support-muted:#b9c9dd;--support-field:#121d2c;--support-soft:#2b4057;--support-border:#526479;color-scheme:dark}
.support-dialog h2{font-size:1.25rem;color:var(--support-text)!important}
.support-dialog>p:not(.alert),.support-dialog label{color:var(--support-text)!important}
.support-dialog .muted{color:var(--support-muted)!important}
.support-dialog fieldset{border:0;padding:0;margin:0}
.support-dialog input{margin:8px 0;background:var(--support-field)!important;color:var(--support-text)!important;border-color:var(--support-border)!important;-webkit-text-fill-color:var(--support-text)}
.support-dialog input:focus{border-color:#6697ed!important;box-shadow:0 0 0 3px #3b82f633}
.support-dialog .btn-light{background:var(--support-soft)!important;color:var(--support-text)!important;border-color:var(--support-border)!important}
.support-dialog .btn-light:hover{filter:brightness(.94)}
.support-dialog .btn-primary{background:#285fd8!important;border-color:#285fd8!important;color:#fff!important}
.support-dialog .btn-primary:hover{background:#204eb5!important;border-color:#204eb5!important}
.support-dialog .btn-outline-primary{background:transparent!important;color:var(--support-text)!important;border-color:#6697ed!important}
.support-dialog .alert-danger{background:#fff0f1!important;color:#912339!important;border-color:#ebbbc4!important}
.support-dialog .alert-success{background:#e9f7ef!important;color:#225f3b!important;border-color:#abd5bb!important}
.support-dialog .alert-info{background:#eaf3ff!important;color:#204779!important;border-color:#bad0ee!important}
</style>
