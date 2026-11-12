<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue';
import {api,invalidateCatalog} from './api';
import QuestionContent from './QuestionContent.vue';
import BusyFeedback from './BusyFeedback.vue';
const props=defineProps({paperId:Number,paperName:String});const emit=defineEmits(['close','saved']);
const rows=ref([]),selected=ref(0),busy=ref(false),error=ref(''),message=ref('');let baseline=[];
const current=computed(()=>rows.value[selected.value]);
const changed=computed(()=>rows.value.map((r,i)=>JSON.stringify(r)!==baseline[i]?i:-1).filter(i=>i>=0));
function close(){if(!busy.value&&(!changed.value.length||confirm('Discard all unsaved paper corrections?')))emit('close')}
function unloading(e){if(changed.value.length){e.preventDefault();e.returnValue=''}}
onBeforeUnmount(()=>window.removeEventListener('beforeunload',unloading));
onMounted(async()=>{busy.value=true;window.addEventListener('beforeunload',unloading);try{
 const d=await api(`/admin/papers/${props.paperId}/questions/edit`);
 rows.value=d.items.map(r=>({...r.question,updated_at:r.updated_at,status:r.status,passage:r.question.passage||'',explanation:r.question.explanation||'',topic:r.question.topic||'',options:r.question.options.map(o=>({...o})),answerJSON:JSON.stringify(r.question.answers??null)}));
 baseline=rows.value.map(r=>JSON.stringify(r));
}catch(e){error.value=e.message}finally{busy.value=false}});
async function save(){if(busy.value||!changed.value.length)return;error.value='';message.value='';try{
 const questions=changed.value.map(i=>{const r=rows.value[i];let answers;try{answers=JSON.parse(r.answerJSON)}catch{selected.value=i;throw Error(`Question ${r.number}: invalid answer JSON.`)}
 return {id:r.id,updated_at:r.updated_at,kind:r.kind,text:r.text,passage:r.passage,answers,explanation:r.explanation,topic:r.topic,marks:r.marks===''?null:r.marks,negative_marks:r.negative_marks===''?null:r.negative_marks,tolerance:r.tolerance===''?0:r.tolerance,options:['MCQ','MSQ','TRUE_FALSE'].includes(r.kind)?r.options:[]}});
 if(new TextEncoder().encode(JSON.stringify({questions})).length>2000000)throw Error('This batch is too large. Save fewer changes.');
 busy.value=true;const d=await api(`/admin/papers/${props.paperId}/questions/edit`,{method:'PATCH',body:{questions}});
 for(const saved of d.saved){const i=rows.value.findIndex(r=>r.id===saved.id);rows.value[i].updated_at=saved.updated_at;baseline[i]=JSON.stringify(rows.value[i])}
 invalidateCatalog();message.value=`${d.saved.length} questions updated together.`;emit('saved');
}catch(e){error.value=e.message}finally{busy.value=false}}
</script>
<template><div class="modal-backdrop-custom"><section class="content-editor panel" role="dialog" aria-modal="true" aria-labelledby="paper-editor-title" @keydown.esc.stop="close">
<div class="section-row"><h2 id="paper-editor-title">Edit paper questions</h2><button class="btn btn-light" :disabled="busy" @click="close">Close</button></div><p>{{paperName}}</p>
<p class="small muted">Edit several questions, then save all changes together. Hidden questions remain hidden. Existing attempts keep their original snapshots.</p>
<p v-if="error" class="alert alert-danger" role="alert">{{error}}</p><p v-if="message" class="alert alert-success" role="status">{{message}}</p><BusyFeedback v-if="busy" label="Working…"/>
<template v-if="rows.length"><nav class="d-flex gap-2 flex-wrap mb-3" aria-label="Choose question to edit"><button v-for="(r,i) in rows" :key="r.id" type="button" class="btn" :class="selected===i?'btn-primary':'btn-light'" :disabled="busy" @click="selected=i">Q{{r.number}}{{changed.includes(i)?' *':''}}{{r.status==='HIDDEN'?' (hidden)':''}}</button></nav>
<form @submit.prevent="save"><fieldset :disabled="busy"><div class="editor-columns"><div><div class="form-grid"><label>Paper question number<input disabled class="form-control" aria-label="Paper question number" v-model="current.number" maxlength="40" placeholder="e.g. 14" required></label><label>Question type<select class="form-select" aria-label="Question type" v-model="current.kind"><option v-for="kind in ['MCQ','MSQ','NAT','TRUE_FALSE','SHORT_TEXT','SUBJECTIVE','IMAGE']">{{kind}}</option></select></label></div>
<label>Shared passage (optional)<textarea class="form-control" v-model="current.passage" maxlength="20000" rows="2"></textarea></label>
<label>Question text / formulas<textarea class="form-control" aria-label="Question text" v-model="current.text" maxlength="20000" rows="5" required></textarea><small>Use \(x^2\) for inline maths. Existing images are preserved. Use the single-question editor to upload or remove images.</small></label>
<template v-if="['MCQ','MSQ','TRUE_FALSE'].includes(current.kind)"><label>Options</label><div v-for="(o,n) in current.options" :key="n" class="edit-option"><input class="form-control" aria-label="Option key" v-model="o.key" maxlength="20" required><textarea class="form-control" aria-label="Option text" v-model="o.text" maxlength="10000" required></textarea><button class="btn btn-light" type="button" @click="current.options.splice(n,1)">Remove</button></div><button class="btn btn-light" type="button" :disabled="current.options.length>=20" @click="current.options.push({key:String.fromCharCode(65+current.options.length),text:''})">Add option</button></template>
<label>Correct answer (JSON)<input class="form-control" aria-label="Correct answer" v-model="current.answerJSON"><small>MCQ: ["A"] · MSQ: ["A","B"] · NAT: 2.5 · Unknown: null. Leave unknown keys as null.</small></label>
<div class="form-grid"><label>Marks<input class="form-control" type="number" min="0" step="any" v-model.number="current.marks"></label><label>Negative marks<input class="form-control" type="number" min="0" step="any" v-model.number="current.negative_marks"></label><label>NAT tolerance<input class="form-control" type="number" min="0" step="any" v-model.number="current.tolerance"></label><label>Topic<input class="form-control" maxlength="150" v-model="current.topic"></label></div>
<label>Explanation<textarea class="form-control" v-model="current.explanation" maxlength="20000" rows="2"></textarea></label></div><aside><h3>Preview selected question</h3><QuestionContent :text="[current.passage,current.text].filter(Boolean).join('\n\n')" :images="current.images.filter(i=>!i.option_key)"/><div v-for="o in (['MCQ','MSQ','TRUE_FALSE'].includes(current.kind)?current.options:[])" class="review-option"><strong>{{o.key}}.</strong><QuestionContent :text="o.text" :images="current.images.filter(i=>i.option_key===o.key)"/></div></aside></div>
<div class="dialog-actions"><button type="button" class="btn btn-light" :disabled="busy||selected===0" @click="selected--">Previous question</button><button type="button" class="btn btn-light" :disabled="busy||selected===rows.length-1" @click="selected++">Next question</button><button class="btn btn-primary" :disabled="busy||!changed.length">Save all changes ({{changed.length}})</button></div></fieldset></form></template><p v-else-if="!busy&&!error">No editable questions in this paper.</p></section></div></template>