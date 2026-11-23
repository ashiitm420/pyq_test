<script setup>
import {ref,computed,onMounted,onUnmounted} from 'vue';
import {api,go,session} from './api';
import {displayExamTitle} from './displayTitle';
import SearchableSelect from './SearchableSelect.vue';
const courses=ref([]),exams=ref([]),course=ref(''),exam=ref(''),query=ref(''),rows=ref([]),selected=ref([]),page=ref(1),total=ref(0),mode=ref('exam'),minutes=ref(120),busy=ref(false),loading=ref(false),error=ref('');
const admission=ref(null),remaining=ref(0);
const isAdmin=computed(()=>session.user?.role==='ADMIN');
const allowed=computed(()=>isAdmin.value||session.customExamBeta);
let stopped=false,generation=0,retryTimer;
function clearAdmission(){
 clearInterval(retryTimer);admission.value=null;remaining.value=0;
}
function showAdmission(failure){
 clearAdmission();
 const details=failure.details||{};
 admission.value={...details,code:failure.code,message:failure.message};
 if(!details.retry_after_seconds)return;
 const retryAt=Date.now()+details.retry_after_seconds*1000;
 const update=()=>{
  remaining.value=Math.max(0,Math.ceil((retryAt-Date.now())/1000));
  if(!remaining.value)clearAdmission();
 };
 update();retryTimer=setInterval(update,1000);
}
const retryText=computed(()=>{
 const total=remaining.value,hours=Math.floor(total/3600),mins=Math.floor(total%3600/60),seconds=total%60;
 if(hours)return hours+'h '+mins+'m '+seconds+'s';
 if(mins)return mins+'m '+seconds+'s';
 return seconds+(seconds===1?' second':' seconds');
});
const questionCount=computed(()=>selected.value.reduce((n,p)=>n+p.question_count,0));
const valid=computed(()=>selected.value.length>0&&questionCount.value<=125&&Number.isInteger(Number(minutes.value))&&minutes.value>=1&&minutes.value<=480);
const options=computed(()=>courses.value.map(c=>({value:c.id,label:c.name+(c.code?' · '+c.code:'')})));
const source=p=>p.canonical_paper_id||p.id;
const chosen=p=>selected.value.some(s=>source(s)===source(p));
function toggle(p){if(busy.value)return;if(chosen(p)){selected.value=selected.value.filter(s=>source(s)!==source(p));return}if(selected.value.length<4&&questionCount.value+p.question_count<=125)selected.value.push(p)}
async function load(reset=false){if(reset)page.value=1;const n=++generation;loading.value=true;error.value='';try{const d=await api('/papers?'+new URLSearchParams({course_id:course.value,exam_type_id:exam.value,q:query.value,available:'true',page:page.value,limit:12}));if(!stopped&&n===generation){rows.value=d.items;total.value=d.total}}catch(e){if(!stopped&&n===generation)error.value=e.message}finally{if(!stopped&&n===generation)loading.value=false}}
const startBlocked=computed(()=>{
 const failure=admission.value;
 if(!failure)return false;
 if(failure.code==='CUSTOM_DAILY_QUOTA')return questionCount.value>failure.questions_left;
 return remaining.value>0||failure.code==='CUSTOM_UNFINISHED';
});
async function start(){
 if(busy.value||!valid.value||startBlocked.value)return;
 if(isAdmin.value&&!window.confirm('Start this admin-only custom exam? It replaces your unfinished attempt in this browser.'))return;
 clearAdmission();busy.value=true;error.value='';
 try{
  const a=await api('/attempts',{method:'POST',body:{paper_ids:selected.value.map(p=>p.id),mode:mode.value,duration_seconds:Number(minutes.value)*60}});
  if(!stopped)go('/attempt/'+a.id);
 }catch(e){
  if(!stopped){
   if(e.code?.startsWith('CUSTOM_')||e.code==='START_BUSY')showAdmission(e);
   else error.value=e.message;
  }
 }finally{if(!stopped)busy.value=false}
}
async function discardUnfinished(){
 const id=admission.value?.attempt_id;
 if(!id||busy.value||!window.confirm('Discard this unfinished attempt and its saved responses?'))return;
 busy.value=true;error.value='';
 try{
  await api('/attempts/'+id,{method:'DELETE'});
  if(!stopped)clearAdmission();
 }catch(e){if(!stopped)error.value=e.message}
 finally{if(!stopped)busy.value=false}
}
onMounted(async()=>{
 if(!allowed.value)return;
 try{
  const d=await api('/catalog');if(stopped)return;
  courses.value=d.courses||[];exams.value=d.meta?.exams||[];await load();
 }catch(e){if(!stopped)error.value=e.message}
});
onUnmounted(()=>{stopped=true;generation++;clearInterval(retryTimer)});

</script>
<template><section v-if="allowed" class="panel"><h2>Create Custom Exam <small class="beta-tag">{{isAdmin ? 'Admin test' : 'BETA'}}</small></h2><p v-if="!isAdmin" class="muted">Daily availability is limited during beta.</p><p>Choose up to 4 papers, maximum 125 questions total. Switch papers and exam/practice modes freely. Exam time pauses in practice and resumes with the remaining budget. No AI generation or background processing. Results remain temporary and do not change single-paper scores or student analytics.</p><p v-if="error" role="alert" class="alert alert-danger">{{error}}</p><fieldset :disabled="busy"><form class="custom-filters" @submit.prevent="load(true)"><label>Course<SearchableSelect v-model="course" :options="[{value:'',label:'All courses'},...options]" aria-label="Custom exam course" @change="load(true)"/></label><label>Exam<select class="form-select" v-model="exam" @change="load(true)"><option value="">All quizzes / ET</option><option v-for="e in exams" :key="e.id" :value="e.id">{{e.name}}</option></select></label><label>Search paper / term<input class="form-control" v-model="query" maxlength="150"></label><button class="btn btn-light" :disabled="loading">Search</button></form><p v-if="loading" role="status">Loading paper list…</p><article v-for="p in rows" :key="p.id" class="custom-paper"><label><input type="checkbox" :checked="chosen(p)" :disabled="!chosen(p)&&(selected.length>=4||questionCount+p.question_count>125)" @change="toggle(p)"> <strong>{{p.course}} · {{p.exam}} · {{p.term}} {{p.session}}</strong><br>{{displayExamTitle(p.name)==='Practice session'?'':displayExamTitle(p.name)}} · {{p.question_count}} questions · {{p.total_marks??'Unknown'}} marks</label></article><p v-if="!loading&&!rows.length">No available papers match.</p><div class="d-flex gap-3"><button class="btn btn-light" :disabled="page===1||loading" @click="page--;load()">Previous</button><span>Page {{page}} · {{total}} papers</span><button class="btn btn-light" :disabled="page*12>=total||loading" @click="page++;load()">Next</button></div><h3 class="mt-3">Selected: {{selected.length}} / 4 · {{questionCount}} / 125 questions</h3><ol><li v-for="p in selected" :key="p.id">{{p.course}} · {{p.exam}} · {{p.term}} <button class="text-btn" @click="toggle(p)">Remove</button></li></ol><label>Start mode<select class="form-select" aria-label="Custom exam start mode" v-model="mode"><option value="exam">Exam (timed)</option><option value="practice">Practice (untimed)</option></select></label><label>Exam time budget (minutes)<input class="form-control" type="number" min="1" max="480" step="1" v-model="minutes"></label><p class="muted small">All questions retain their source marking. Missing keys/marks remain ungraded. Large selections above the 1 MiB content limit are rejected without truncating papers.</p><section v-if="admission" class="alert alert-warning mt-3" aria-label="Custom Exam availability">
 <p class="mb-0" role="status">{{admission.message}}<template v-if="admission.code==='CUSTOM_DAILY_QUOTA'"> The quota resets at 12:00 AM IST.</template></p>
 <p v-if="remaining" class="mb-0">Try again in {{retryText}}.</p>
 <div v-if="admission.attempt_id" class="d-flex gap-2 flex-wrap mt-2">
  <a class="btn btn-outline-primary" :href="'/attempt/'+admission.attempt_id">Open unfinished attempt</a>
  <button type="button" class="btn btn-light" @click="discardUnfinished">Discard unfinished attempt</button>
 </div>
</section>
<button class="btn btn-primary mt-3" :disabled="!valid||busy||startBlocked" @click="start">{{busy?'Starting…':'Start custom exam'}}</button></fieldset></section></template>
<style scoped>.beta-tag{display:inline-block;border:1px solid var(--line);border-radius:6px;padding:.2em .45em;vertical-align:middle;font-size:.6em}fieldset{border:0;padding:0}.custom-filters{display:flex;gap:12px;flex-wrap:wrap;align-items:end}.custom-filters label{flex:1;min-width:180px}.custom-paper{padding:12px 0;border-bottom:1px solid var(--line)}small{font-size:.7em}input[type=number]{max-width:180px}</style>
