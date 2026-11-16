<script setup>
import {ref,onMounted,onUnmounted,nextTick,defineAsyncComponent} from 'vue';
import {api} from './api';
import {promptFor,rememberPrompt,readPreference,savePreference,markFeedbackSubmitted} from './engagement';
const props=defineProps({attempt:Object});const emit=defineEmits(['feedback']);
const kind=ref(null),checkout=ref(false),dialog=ref(null);let active=true,previousFocus;
const SupportCheckout=defineAsyncComponent(()=>import('./SupportCheckout.vue'));
function close(){if(kind.value==='feedback')savePreference('feedback-skip',Date.now());kind.value=null;previousFocus?.focus?.()}
function feedback(){close();emit('feedback')}
function support(){close();checkout.value=true}
function keys(e){if(!kind.value)return;if(e.key==='Escape')close();if(e.key==='Tab'){const buttons=dialog.value?.querySelectorAll('button');if(!buttons?.length)return;const first=buttons[0],last=buttons[buttons.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}}
onMounted(async()=>{
 if(!promptFor(props.attempt))return;
 // Reconcile a successful prior submission from the signed browser identity.
 if(!readPreference('feedback-submitted',false)){
  try{const d=await api('/feedback/state');if(d.submitted)markFeedbackSubmitted()}catch{return}
 }
 if(!active)return;
 kind.value=promptFor(props.attempt);
 if(kind.value){rememberPrompt(props.attempt.id,kind.value);previousFocus=document.activeElement;await nextTick();dialog.value?.querySelector('button')?.focus()}
 document.addEventListener('keydown',keys);
});
onUnmounted(()=>{active=false;document.removeEventListener('keydown',keys)});
</script>
<template><div v-if="kind" class="modal-backdrop-custom" @click.self="close"><section ref="dialog" class="confirm-dialog panel" role="dialog" aria-modal="true" aria-labelledby="post-attempt-heading"><span class="eyebrow">{{kind==='feedback'?'THANK YOU FOR PRACTISING':'KEEP MAURYAHUB FREE'}}</span><h2 id="post-attempt-heading">{{kind==='feedback'?'How was your experience?':'Help the next student prepare.'}}</h2><p>{{kind==='feedback'?'Your feedback helps us improve MauryaHub for everyone.':'If MauryaHub helped you, an optional contribution supports hosting and maintenance. Every feature stays free.'}}</p><div class="d-flex gap-3 flex-wrap"><button class="btn btn-primary" @click="kind==='feedback'?feedback():support()">{{kind==='feedback'?'Give Feedback':'Support MauryaHub ☕'}}</button><button class="btn btn-light" @click="close">Skip for Now</button></div><button v-if="kind==='feedback'" class="text-btn mt-3" @click="support">You can also support MauryaHub ☕</button></section></div><SupportCheckout v-if="checkout" @close="checkout=false"/></template>
