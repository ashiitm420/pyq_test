<script setup>
import {ref,computed} from 'vue';
import {api,invalidateCatalog} from './api';
import QuestionContent from './QuestionContent.vue';
import BusyFeedback from './BusyFeedback.vue';
const props=defineProps({paperId:Number,paperName:String});
const emit=defineEmits(['close','saved','edit']);
const blank=()=>({number:'',kind:'MCQ',text:'',passage:'',options:[{key:'A',text:''},{key:'B',text:''}],answerJSON:'null',marks:null,negative_marks:0,tolerance:0,explanation:'',topic:''});
const rows=ref([blank()]),selected=ref(0),publish=ref(false),busy=ref(false),error=ref(''),result=ref(null);
const current=computed(()=>rows.value[selected.value]);
let requestId=crypto.randomUUID(),lastPayload='';
function add(){if(rows.value.length>=20||busy.value)return;rows.value.push(blank());selected.value=rows.value.length-1}
function remove(){if(rows.value.length<2||busy.value)return;rows.value.splice(selected.value,1);selected.value=Math.min(selected.value,rows.value.length-1)}
function close(){if(!busy.value&&(result.value||confirm('Close and discard this unsaved question batch?')))emit('close')}
async function save(){
 if(busy.value||result.value)return;error.value='';
 try{
  const questions=rows.value.map((row,i)=>{
   if(!row.number.trim()||!row.text.trim())throw Error(`Question ${i+1}: enter its paper number and text.`);
   let answers;try{answers=JSON.parse(row.answerJSON)}catch{throw Error(`Question ${i+1}: invalid answer JSON.`)}
   const {answerJSON,...fields}=row;
   return {...fields,answers,options:['MCQ','MSQ','TRUE_FALSE'].includes(row.kind)?row.options:[],marks:row.marks===''?null:row.marks,negative_marks:row.negative_marks===''?0:row.negative_marks,tolerance:row.tolerance===''?0:row.tolerance};
  });
  if(new Set(questions.map(q=>q.number.trim().toLowerCase())).size!==questions.length)throw Error('Question numbers must be unique.');
  const body={questions,publish:publish.value},payload=JSON.stringify(body);
  if(new TextEncoder().encode(payload).length>250000)throw Error('This batch is too large. Add fewer questions.');
  if(lastPayload&&lastPayload!==payload)requestId=crypto.randomUUID();lastPayload=payload;
  busy.value=true;
  result.value=await api(`/admin/papers/${props.paperId}/questions/append`,{method:'POST',body:{...body,request_id:requestId}});
  invalidateCatalog();emit('saved');
 }catch(e){error.value=e.message}finally{busy.value=false}
}
</script>
<template><div class="modal-backdrop-custom"><section class="content-editor panel" role="dialog" aria-modal="true" aria-labelledby="append-title" @keydown.esc.stop="close">
<div class="section-row"><h2 id="append-title">Add / append questions</h2><button class="btn btn-light" :disabled="busy" @click="close">Close</button></div>
<p>{{paperName||'Selected paper'}}</p><p class="muted small">Add only missing questions. Existing questions and active attempts stay unchanged. Use the original paper numbers; no automatic renumbering. This form adds text/formulas and options, not a replacement PDF.</p>
<p v-if="error" class="alert alert-danger" role="alert">{{error}}</p>
<div v-if="result" class="alert alert-success" role="status"><strong>{{result.ids.length}} questions saved{{publish?' and published':' as hidden drafts'}}.</strong><p>For each question, open the editor to add images or make corrections. For drafts, finish reviewing and choose Restore question to publish.</p><button v-for="(id,n) in result.ids" :key="id" class="btn btn-light me-2" @click="emit('edit',id)">Edit question {{rows[n].number}} / add image</button></div>
<template v-else><div class="d-flex gap-2 flex-wrap mb-3"><button v-for="(row,n) in rows" :key="n" class="btn" :class="selected===n?'btn-primary':'btn-light'" :disabled="busy" @click="selected=n">{{row.number||'New '+(n+1)}}</button><button class="btn btn-light" :disabled="busy||rows.length>=20" @click="add">+ Add another</button><button class="btn btn-light" :disabled="busy||rows.length===1" @click="remove">Remove selected draft</button></div>
<form @submit.prevent="save"><fieldset :disabled="busy"><div class="editor-columns"><div><div class="form-grid"><label>Paper question number<input class="form-control" aria-label="Paper question number" v-model="current.number" maxlength="40" placeholder="e.g. 14" required></label><label>Question type<select class="form-select" aria-label="Question type" v-model="current.kind"><option v-for="kind in ['MCQ','MSQ','NAT','TRUE_FALSE','SHORT_TEXT','SUBJECTIVE','IMAGE']">{{kind}}</option></select></label></div>
<label>Shared passage (optional)<textarea class="form-control" v-model="current.passage" maxlength="20000" rows="2"></textarea></label>
<label>Question text / formulas<textarea class="form-control" aria-label="Question text" v-model="current.text" maxlength="20000" rows="5" required></textarea><small>Use \(x^2\) for inline maths. For image-based questions, add a short description, save as draft, then upload the image in the editor.</small></label>
<template v-if="['MCQ','MSQ','TRUE_FALSE'].includes(current.kind)"><label>Options</label><div v-for="(o,n) in current.options" :key="n" class="edit-option"><input class="form-control" aria-label="Option key" v-model="o.key" maxlength="20" required><textarea class="form-control" aria-label="Option text" v-model="o.text" maxlength="10000" required></textarea><button class="btn btn-light" type="button" @click="current.options.splice(n,1)">Remove</button></div><button class="btn btn-light" type="button" :disabled="current.options.length>=20" @click="current.options.push({key:String.fromCharCode(65+current.options.length),text:''})">Add option</button></template>
<label>Correct answer (JSON)<input class="form-control" aria-label="Correct answer" v-model="current.answerJSON"><small>MCQ: ["A"] · MSQ: ["A","B"] · NAT: 2.5 · Unknown: null. Leave unknown keys as null.</small></label>
<div class="form-grid"><label>Marks<input class="form-control" type="number" min="0" step="any" v-model.number="current.marks"></label><label>Negative marks<input class="form-control" type="number" min="0" step="any" v-model.number="current.negative_marks"></label><label>NAT tolerance<input class="form-control" type="number" min="0" step="any" v-model.number="current.tolerance"></label><label>Topic<input class="form-control" maxlength="150" v-model="current.topic"></label></div>
<label>Explanation<textarea class="form-control" v-model="current.explanation" maxlength="20000" rows="2"></textarea></label></div><aside><h3>Preview selected question</h3><QuestionContent :text="[current.passage,current.text].filter(Boolean).join('\n\n')" :images="[]"/><div v-for="o in (['MCQ','MSQ','TRUE_FALSE'].includes(current.kind)?current.options:[])" class="review-option"><strong>{{o.key}}.</strong><QuestionContent :text="o.text" :images="[]"/></div></aside></div>
<label class="sync-choice mt-3"><input type="checkbox" v-model="publish"><span>Publish all added questions immediately. Leave unchecked to review hidden drafts and add images first.</span></label>
<div class="dialog-actions"><button class="btn btn-primary" :disabled="busy"><BusyFeedback v-if="busy" label="Adding questions…"/><template v-else>Append {{rows.length}} {{rows.length===1?'question':'questions'}}</template></button></div></fieldset></form></template>
</section></div></template>
