<script setup>
// Admin home: what needs attention today, key numbers and quick actions.
// Uses existing admin-only endpoints; every request is optional so one slow or
// failing source never blanks the whole page.
import {ref,computed,onMounted,onUnmounted} from 'vue';
import {Flag,Inbox,TriangleAlert,Sparkles,Upload,Activity,ScanSearch,FileText,Users,PlayCircle,CircleCheck,TrendingUp,ArrowUpRight,Layers} from 'lucide-vue-next';
import {api} from './api';
const props=defineProps({stats:{type:Object,default:()=>({})},busy:Boolean});
const emit=defineEmits(['navigate','queue']);
const reports=ref(null),messages=ref(null),solutions=ref(null),usage=ref(null),loading=ref(true);let stopped=false;
const optional=p=>api(p).catch(()=>null);
async function load(){
 loading.value=true;
 const [r,m,s,a]=await Promise.all([
  optional('/admin/content-reports?status=OPEN&page=1&limit=1'),
  optional('/admin/contact-messages?status=OPEN'),
  optional('/admin/ai-solutions/summary'),
  optional('/admin/analytics?period=7d'),
 ]);
 if(stopped)return;
 reports.value=r?.total??null;messages.value=m?.total??null;solutions.value=s?.statistics||null;usage.value=a||null;loading.value=false;
}
onMounted(load);onUnmounted(()=>{stopped=true});
const n=v=>(v===null||v===undefined)?'—':Number(v).toLocaleString('en-IN');
const attention=computed(()=>[
 {key:'reports',label:'Open content reports',value:reports.value,tab:'Content Reports',icon:Flag,tone:'rose',hint:'Students flagged formatting issues'},
 {key:'messages',label:'Unread messages',value:messages.value,tab:'Contact Inbox',icon:Inbox,tone:'amber',hint:'Contact and site feedback'},
 {key:'failed',label:'Failed processing',value:props.stats.failed??null,tab:'Processing',icon:TriangleAlert,tone:'red',hint:'Papers that need a retry'},
 {key:'review',label:'Solutions to review',value:solutions.value?(solutions.value.questions_review??0):null,tab:'Solutions',icon:Sparkles,tone:'violet',hint:'Uploaded, not yet published'},
]);
const library=computed(()=>[
 {label:'Papers',value:props.stats.papers,icon:FileText},
 {label:'Processed',value:props.stats.processed,icon:CircleCheck},
 {label:'Available questions',value:props.stats.questions,icon:Layers},
 {label:'In queue',value:(props.stats.queued??0)+(props.stats.active_processing??0),icon:Activity},
]);
const totals=computed(()=>usage.value?.totals||{});
const trend=computed(()=>(usage.value?.trend||[]).slice(-7));
const peak=computed(()=>Math.max(1,...trend.value.map(d=>d.starts||0)));
const coverage=computed(()=>{const s=solutions.value;if(!s||!s.questions_total)return null;return Math.round(100*(s.questions_published||0)/s.questions_total)});
const day=iso=>new Date(iso+'T00:00:00').toLocaleDateString('en-IN',{weekday:'short'});
</script>
<template>
<div class="adm-overview">
 <section aria-labelledby="attention-title">
  <div class="adm-section-head"><h2 id="attention-title">Needs attention</h2><button type="button" class="adm-link" @click="load">Refresh</button></div>
  <div class="adm-attention">
   <button v-for="a in attention" :key="a.key" type="button" class="adm-attn" :class="['tone-'+a.tone,{clear:a.value===0}]" @click="emit('navigate',a.tab)">
    <span class="adm-attn-icon"><component :is="a.icon" :size="18"/></span>
    <span class="adm-attn-body"><span class="adm-attn-label">{{a.label}}</span><strong>{{loading&&a.value===null?'…':n(a.value)}}</strong><small>{{a.value===0?'All clear':a.hint}}</small></span>
    <ArrowUpRight :size="16" class="adm-attn-go"/>
   </button>
  </div>
 </section>

 <div class="adm-grid-2">
  <section class="adm-card" aria-labelledby="usage-title">
   <div class="adm-card-head"><div><h2 id="usage-title">Student activity</h2><p>Last 7 days · IST</p></div><button type="button" class="adm-link" @click="emit('navigate','Analytics')">Full analytics →</button></div>
   <div class="adm-kpis">
    <div><span><Users :size="15"/> Active browsers</span><strong>{{n(totals.active_browsers)}}</strong></div>
    <div><span><PlayCircle :size="15"/> Tests started</span><strong>{{n(totals.starts)}}</strong></div>
    <div><span><CircleCheck :size="15"/> Submitted</span><strong>{{n(totals.completions)}}</strong></div>
    <div><span><TrendingUp :size="15"/> Completion</span><strong>{{totals.completion_rate!=null?totals.completion_rate+'%':'—'}}</strong></div>
   </div>
   <div v-if="trend.length" class="adm-bars" role="img" :aria-label="'Tests started per day: '+trend.map(d=>day(d.day)+' '+(d.starts||0)).join(', ')">
    <div v-for="d in trend" :key="d.day" class="adm-bar"><span class="adm-bar-val">{{d.starts||0}}</span><i :style="{height:Math.max(4,Math.round(100*(d.starts||0)/peak))+'%'}"></i><span class="adm-bar-day">{{day(d.day)}}</span></div>
   </div>
   <p v-else class="adm-empty">{{loading?'Loading activity…':'No activity recorded yet.'}}</p>
  </section>

  <section class="adm-card" aria-labelledby="library-title">
   <div class="adm-card-head"><div><h2 id="library-title">Question library</h2><p>Processing and published solutions</p></div><button type="button" class="adm-link" @click="emit('navigate','Papers')">Manage papers →</button></div>
   <div class="adm-lib">
    <div v-for="l in library" :key="l.label"><component :is="l.icon" :size="16"/><span>{{l.label}}</span><strong>{{n(l.value)}}</strong></div>
   </div>
   <div class="adm-progress" v-if="coverage!==null">
    <div class="adm-progress-head"><span>Solution coverage</span><strong>{{coverage}}%</strong></div>
    <div class="adm-progress-track"><i :style="{width:coverage+'%'}"></i></div>
    <small>{{n(solutions.questions_published)}} of {{n(solutions.questions_total)}} questions have a published solution</small>
   </div>
  </section>
 </div>

 <section class="adm-card" aria-labelledby="actions-title">
  <div class="adm-card-head"><div><h2 id="actions-title">Quick actions</h2><p>Common tasks in one click</p></div></div>
  <div class="adm-actions">
   <button type="button" class="adm-action" @click="emit('navigate','Upload PDFs')"><Upload :size="18"/><span><strong>Upload a PDF</strong><small>Add a new paper to the library</small></span></button>
   <button type="button" class="adm-action" :disabled="busy" @click="emit('queue')"><Activity :size="18"/><span><strong>Queue next 20 pending</strong><small>Process catalog papers in a bounded batch</small></span></button>
   <button type="button" class="adm-action" @click="emit('navigate','Content Quality')"><ScanSearch :size="18"/><span><strong>Scan content quality</strong><small>Find formatting and key problems</small></span></button>
   <button type="button" class="adm-action" @click="emit('navigate','Solutions')"><Sparkles :size="18"/><span><strong>Import solutions</strong><small>Upload, review and publish explanations</small></span></button>
  </div>
 </section>
</div>
</template>
