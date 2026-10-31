<script setup>
import {ref,watch,computed,onBeforeUnmount} from 'vue';import {api} from './api';import MathText from './MathText.vue';
const props=defineProps({paperIds:{type:Array,default:()=>[]}});const emit=defineEmits(['saved']);
const text=ref(''),replace=ref(false),busy=ref(false),error=ref(''),notice=ref(''),rows=ref([]),validated=ref(''),phase=ref(''),key=ref('');
const records=ref({}),paused=ref(false);let disposed=false;
const completed=computed(()=>Object.values(records.value).filter(r=>r.state==='done').length);
const failed=computed(()=>Object.values(records.value).filter(r=>r.state==='failed').length);
const counts=computed(()=>Object.values(records.value).reduce((a,r)=>({published:a.published+(r.published||0),review:a.review+(r.needs_review||0)}),{published:0,review:0}));
watch([text,replace],()=>{rows.value=[];validated.value='';records.value={};key.value='';notice.value=''});
onBeforeUnmount(()=>{disposed=true;paused.value=true});
async function run(fn){if(busy.value)return;busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false;phase.value=''}}
function exportBundle(){window.location.href='/api/admin/ai-solutions/bundle/export?ids='+props.paperIds.join(',')}
function parse(){
 if(new Blob([text.value]).size>100000000)throw Error('Use a JSON file below 100 MB.');
 const b=JSON.parse(text.value);if(b?.format!=='pyq-solutions-bundle-v1'||!Array.isArray(b.papers)||b.papers.length<1||b.papers.length>50)throw Error('Use a bundle containing 1–50 papers.');
 const ids=b.papers.map(p=>p?.paper_id);if(ids.some(id=>!Number.isInteger(id))||new Set(ids).size!==ids.length)throw Error('Paper IDs must be unique integers.');
 return b;
}
async function readFile(event){await run(async()=>{const f=event.target.files?.[0];if(!f)return;if(f.size>100000000)throw Error('Use a JSON file below 100 MB.');text.value=await f.text()})}
async function checkpointKey(){const bytes=new TextEncoder().encode(text.value+'\nreplace='+replace.value);const hash=await crypto.subtle.digest('SHA-256',bytes);return 'pyq:solution-upload:v1:'+Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('')}
function persist(){try{localStorage.setItem(key.value,JSON.stringify(records.value))}catch{notice.value='Browser could not save progress. Keep this page open; the same file can still be retried safely.'}}
async function request(paper,save=false){
 const d=await api('/admin/ai-solutions/bundle/import',{method:'POST',body:{bundle:{format:'pyq-solutions-bundle-v1',papers:[paper]},replace_existing:replace.value,skip_identical:true,...(save?{save:true,publish:true}:{})}});
 const result=d.papers?.[0];if(!result)throw Error('No paper result received. Retry this paper.');if(result.error)throw Error(result.error);return result;
}
async function preview(){await run(async()=>{
 const b=parse();key.value=await checkpointKey();records.value={};
 try{const saved=JSON.parse(localStorage.getItem(key.value)||'{}');for(const p of b.papers)if(saved[p.paper_id]?.state==='done')records.value[p.paper_id]=saved[p.paper_id]}catch{/* A damaged checkpoint must not stop an import. */}
 rows.value=[];
 for(let i=0;i<b.papers.length&&!disposed;i++){
  const p=b.papers[i];phase.value=`Previewing ${i+1} / ${b.papers.length} papers`;
  // Revalidate against current database even when browser progress says completed.
  try{const r=await request(p);rows.value.push(r);if(!r.items.every(q=>q.already_saved))delete records.value[p.paper_id]}
  catch(e){rows.value.push({paper_id:p.paper_id,error:e.message,items:[]});delete records.value[p.paper_id]}
 }
 if(!disposed){validated.value=text.value;notice.value=completed.value?'Saved progress restored. Continue with remaining papers.':'';persist()}
})}
async function save(retryOnly=false){await run(async()=>{
 if(validated.value!==text.value)throw Error('Preview the current bundle first.');const b=parse();paused.value=false;let changed=false;
 for(const p of b.papers){
  if(disposed||paused.value)break;
  if(records.value[p.paper_id]?.state==='done')continue;
  if(retryOnly&&records.value[p.paper_id]?.state!=='failed')continue;
  phase.value=`Processing paper #${p.paper_id}`;
  try{const r=await request(p,true);records.value[p.paper_id]={state:'done',published:r.published||0,needs_review:r.needs_review||0};const index=rows.value.findIndex(x=>x.paper_id===p.paper_id);if(index>=0)rows.value[index]=r;changed=true}
  catch(e){records.value[p.paper_id]={state:'failed',error:e.message}}
  persist();
 }
 notice.value=paused.value?'Paused after the current paper. Resume when ready.':`${completed.value} / ${b.papers.length} papers saved · ${counts.value.published} published · ${counts.value.review} need review · ${failed.value} failed.`;
 if(changed&&!disposed)emit('saved');
})}
</script>
<template><section class="panel mt-3"><h3>Bundled solutions · up to 50 papers</h3>
<p>Select up to 50 papers. Export their questions, available PDFs and detailed-solution prompt. Prepare and check solutions in manageable groups, then upload one combined JSON. Exporting does not generate solutions automatically.</p>
<button class="btn btn-light" :disabled="busy||!paperIds.length||paperIds.length>50" @click="exportBundle">Export selected bundle ({{paperIds.length}} / 50)</button>
<p class="small muted">PDFs included up to 100 MB total; the ZIP lists any missing PDFs. Check all source diagrams before solving.</p>
<p v-if="error" role="alert" class="alert alert-danger">{{error}}</p><p v-if="notice" role="status" class="alert alert-info">{{notice}}</p>
<label class="d-block my-3">Upload bundled solution JSON (up to 100 MB)<input type="file" accept=".json,application/json" class="form-control" :disabled="busy" @change="readFile"></label>
<textarea v-model="text" class="form-control" rows="8" aria-label="Bundled solution JSON" :disabled="busy" placeholder="Paste one pyq-solutions-bundle-v1 JSON here"></textarea>
<label class="d-block my-3"><input type="checkbox" v-model="replace" :disabled="busy"> Replace existing solutions included in this bundle</label>
<div class="d-flex flex-wrap gap-2"><button class="btn btn-light" :disabled="busy||!text" @click="preview">Preview bundle</button><button class="btn btn-primary" :disabled="busy||validated!==text||!rows.some(p=>!p.error&&p.items.length)" @click="save(false)">{{completed?'Resume remaining papers':'Save & Publish valid solutions'}}</button><button v-if="failed" class="btn btn-light" :disabled="busy||validated!==text" @click="save(true)">Retry failed papers ({{failed}})</button><button v-if="busy&&phase.startsWith('Processing')" class="btn btn-light" :disabled="paused" @click="paused=true">Pause after current paper</button></div>
<p v-if="phase" role="status">{{phase}}</p><div v-if="validated"><progress aria-label="Paper upload progress" :value="completed+failed" :max="rows.length||1"></progress><p>{{completed}} / {{rows.length}} papers saved · {{counts.published}} solutions published · {{counts.review}} need review · {{failed}} failed</p></div>
<p class="small muted mt-3">Papers are saved one at a time. After a reload, select the same file and replacement setting, preview, then resume. Progress is stored in this browser; solution text is not. Exact saved solutions are safely skipped on retry. Warnings stay unpublished for review. Checks do not verify mathematical reasoning.</p>
<article v-for="p in rows" :key="p.paper_id" class="panel mt-3"><h4>{{p.paper_name||'Paper'}} #{{p.paper_id}} <span v-if="records[p.paper_id]?.state==='done'">· Saved</span></h4><p v-if="records[p.paper_id]?.state==='failed'||p.error" class="alert alert-danger">{{records[p.paper_id]?.error||p.error}}</p><p v-else>{{p.items.length}} included · {{p.missing}} questions omitted · {{p.items.filter(q=>q.replacing&&!q.already_saved).length}} existing solutions to replace</p><details v-for="q in p.items" :key="q.question_id" @toggle="q.expanded=$event.target.open"><summary>Question {{q.number}} · {{q.already_saved?'Already saved':q.status}}</summary><p>Final answer: {{q.final_answer}}</p><p v-for="check in q.checks" class="alert alert-warning">{{check}}</p><MathText v-if="q.expanded" :text="q.text" inline-dollar/></details></article>
</section></template>
