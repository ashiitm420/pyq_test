<script setup>
// Builds the share image only when the student clicks, entirely in the browser.
import {ref,onUnmounted,nextTick} from 'vue';
import {shareSummary,shareText,buildShareImage,whatsappUrl} from './shareCard';
const props=defineProps({attempt:{type:Object,required:true}});
const open=ref(false),busy=ref(false),error=ref(''),preview=ref(''),notice=ref(''),dialog=ref(null);
let blob=null,file=null;
const summary=()=>shareSummary(props.attempt);
function canShareFile(){try{return !!(file&&navigator.canShare?.({files:[file]}))}catch{return false}}
const nativeShare=ref(false);
async function start(){
 error.value='';notice.value='';open.value=true;
 if(blob){await nextTick();dialog.value?.focus();return}
 busy.value=true;
 try{
  const s=summary();if(!s)throw new Error('Score is not available for this attempt.');
  blob=await buildShareImage(s);
  file=new File([blob],'mauryahub-result.png',{type:'image/png'});
  preview.value=URL.createObjectURL(blob);nativeShare.value=canShareFile();
 }catch(e){error.value=e.message||'Could not create the share image.'}
 finally{busy.value=false;await nextTick();dialog.value?.focus()}
}
async function share(){
 const s=summary();
 try{await navigator.share({files:[file],title:'My MauryaHub result',text:shareText(s)})}
 catch(e){if(e?.name!=='AbortError')error.value='Sharing was not completed. Use Download or WhatsApp instead.'}
}
function download(){
 const a=document.createElement('a');a.href=preview.value;a.download='mauryahub-result.png';document.body.appendChild(a);a.click();a.remove();
 notice.value='Image downloaded. Attach it in WhatsApp or anywhere you like.';
}
function whatsapp(){notice.value='WhatsApp opens with text only. To send the image, download it and attach it in WhatsApp.';window.open(whatsappUrl(shareText(summary())),'_blank','noopener')}
function close(){open.value=false}
onUnmounted(()=>{if(preview.value)URL.revokeObjectURL(preview.value)});
</script>
<template>
<button type="button" class="btn btn-outline-primary share-result-btn" :disabled="busy" @click="start">↗ Share result</button>
<div v-if="open" class="modal-backdrop-custom" @click.self="close" @keydown.esc="close">
 <div ref="dialog" class="panel share-dialog" role="dialog" aria-modal="true" aria-labelledby="share-title" tabindex="-1">
  <div class="section-row"><h2 id="share-title">Share your result</h2><button type="button" class="text-btn" aria-label="Close" @click="close">✕</button></div>
  <p v-if="busy" role="status">Creating your image…</p>
  <p v-if="error" class="alert alert-danger" role="alert">{{error}}</p>
  <img v-if="preview" :src="preview" class="share-preview" alt="Result card showing your score, correct and incorrect answers, and accuracy">
  <p class="muted small mb-3">The image shows only the paper and your score — no name or answers.</p>
  <div class="share-actions" v-if="preview">
   <button v-if="nativeShare" type="button" class="btn btn-primary" @click="share">Share image</button>
   <button type="button" class="btn" :class="nativeShare?'btn-outline-primary':'btn-primary'" @click="whatsapp">WhatsApp text</button>
   <button type="button" class="btn btn-light" @click="download">Download image</button>
  </div>
  <p v-if="notice" class="alert alert-success mt-3 mb-0" role="status">{{notice}}</p>
 </div>
</div>
</template>
<style scoped>
.share-dialog{width:min(460px,100%);max-height:calc(100vh - 40px);overflow:auto;outline:none}
.share-dialog h2{margin:0}
.share-preview{display:block;width:100%;max-width:340px;margin:0 auto 14px;border-radius:12px;border:1px solid var(--line);box-shadow:0 10px 30px #14233b1f}
.share-actions{display:flex;gap:10px;flex-wrap:wrap}.share-actions .btn{flex:1}
</style>
