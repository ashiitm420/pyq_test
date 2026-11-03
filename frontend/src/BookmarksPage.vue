<script setup>
// Bookmarks live only in this browser (localStorage). Grouping, search, sorting
// and undo all run here; the server is used only when a practice is started.
import {ref,computed,onUnmounted} from 'vue';
import {Search,Bookmark,ChevronDown,ExternalLink,PlayCircle,Trash2,BookOpen} from 'lucide-vue-next';
import {api,go} from './api';
import {bookmarkRows,setBookmark,restoreBookmark,clearBookmarks} from './browserStore';
import QuestionContent from './QuestionContent.vue';
const rows=ref([]),query=ref(''),course=ref(''),sort=ref('newest'),openOptions=ref(new Set()),undo=ref(null),error=ref(''),starting=ref(''),limit=ref(30);
let undoTimer;
function load(){rows.value=bookmarkRows().map((q,n)=>({...q,_order:n}))}
load();
const titleOf=q=>q.paper_title||(q.paper_id?'Paper #'+q.paper_id:'Other questions');
const courseOf=q=>q.paper_title?q.paper_title.split(' · ')[0]:'Other';
const courses=computed(()=>[...new Set(rows.value.map(courseOf))].sort((a,b)=>a==='Other'?1:b==='Other'?-1:a.localeCompare(b)));
const searchText=q=>[q.text,q.passage,titleOf(q),'q'+q.number,...(q.options||[]).map(o=>o.text)].filter(Boolean).join(' ').toLowerCase();
const filtered=computed(()=>{
 const words=query.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const list=rows.value.filter(q=>(!course.value||courseOf(q)===course.value)&&(!words.length||words.every(w=>searchText(q).includes(w))));
 const when=q=>q.saved_at||q._order;
 return list.sort((a,b)=>sort.value==='newest'?when(b)-when(a):when(a)-when(b));
});
const visible=computed(()=>filtered.value.slice(0,limit.value));
// Group visible bookmarks by paper, keeping the chosen sort order between groups.
const groups=computed(()=>{const map=new Map();for(const q of visible.value){const k=titleOf(q);if(!map.has(k))map.set(k,{title:k,paper_id:q.paper_id,items:[]});map.get(k).items.push(q)}
 const totals=new Map();for(const q of filtered.value)totals.set(titleOf(q),(totals.get(titleOf(q))||0)+1);
 return [...map.values()].map(g=>({...g,total:totals.get(g.title)}))});
const letter=n=>String.fromCharCode(65+n);
const kind=k=>({MCQ:'MCQ',MSQ:'MSQ',NAT:'Numerical',TRUE_FALSE:'True / False',SHORT_TEXT:'Short answer',SUBJECTIVE:'Subjective'}[k]||k||'Question');
function toggleOptions(id){const s=new Set(openOptions.value);s.has(id)?s.delete(id):s.add(id);openOptions.value=s}
function showUndo(items,label){clearTimeout(undoTimer);undo.value={items,label};undoTimer=setTimeout(()=>{undo.value=null},6000)}
function remove(q){try{setBookmark({id:q.id},false);load();showUndo([q],'Bookmark removed')}catch(e){error.value=e.message}}
function clearAll(){if(!rows.value.length||!confirm('Remove all '+rows.value.length+' bookmarks from this browser?'))return;const saved=rows.value.slice();try{clearBookmarks();load();showUndo(saved,'All bookmarks removed')}catch(e){error.value=e.message}}
function undoRemove(){if(!undo.value)return;try{for(const q of undo.value.items){const {_order,...clean}=q;restoreBookmark(clean)}load()}catch(e){error.value=e.message}clearTimeout(undoTimer);undo.value=null}
async function practice(list,key){if(starting.value)return;starting.value=key;error.value='';try{const ids=list.map(q=>q.id).slice(0,500);const a=await api('/attempts',{method:'POST',body:{collection:'bookmarks',mode:'practice',question_ids:ids}});go('/attempt/'+a.id)}catch(e){error.value=e.message}finally{starting.value=''}}
const studyLink=q=>q.paper_id?'/study/papers/'+q.paper_id+'#question-'+q.id:null;
onUnmounted(()=>clearTimeout(undoTimer));
</script>
<template>
<div class="bm-page">
 <div class="eyebrow">YOUR PRACTICE WORKSPACE</div>
 <div class="section-row bm-head"><div><h1>My bookmarks</h1><p class="muted mb-0"><strong>{{rows.length}}</strong> {{rows.length===1?'question':'questions'}} saved · stored only in this browser</p></div>
  <button v-if="rows.length" class="btn btn-primary" :disabled="!!starting" @click="practice(filtered,'all')"><PlayCircle :size="17"/>{{starting==='all'?'Starting…':filtered.length===rows.length?'Practice all':'Practice these '+filtered.length}}</button></div>
 <p v-if="error" class="alert alert-danger" role="alert">{{error}}</p>

 <div v-if="!rows.length" class="empty panel bm-empty"><Bookmark :size="30"/><h3>No bookmarks yet</h3><p class="muted">While practising, tap <strong>Bookmark</strong> on any question to save it here for revision.</p><a href="/" class="btn btn-primary">Explore papers</a></div>

 <template v-else>
  <div class="bm-toolbar panel">
   <label class="bm-search"><Search :size="17"/><input v-model="query" type="search" class="form-control" placeholder="Search question, option or paper…" aria-label="Search bookmarks"></label>
   <select v-model="course" class="form-select" aria-label="Filter by course"><option value="">All courses</option><option v-for="c in courses" :key="c" :value="c">{{c}}</option></select>
   <select v-model="sort" class="form-select" aria-label="Sort bookmarks"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select>
  </div>
  <p v-if="!filtered.length" class="empty panel">No bookmarks match your search. <button type="button" class="text-btn" @click="query='';course=''">Clear filters</button></p>

  <section v-for="g in groups" :key="g.title" class="bm-group">
   <header class="bm-group-head"><div><h2>{{g.title}}</h2><span class="muted">{{g.total}} {{g.total===1?'bookmark':'bookmarks'}}</span></div>
    <button v-if="g.total>1" type="button" class="btn btn-outline-primary btn-sm" :disabled="!!starting" @click="practice(filtered.filter(q=>titleOf(q)===g.title),g.title)"><PlayCircle :size="15"/>{{starting===g.title?'Starting…':'Practice '+g.total}}</button></header>
   <article v-for="q in g.items" :key="q.id" class="panel bm-card">
    <div class="bm-meta"><span class="bm-qno">Q{{q.number}}</span><span>{{kind(q.kind)}}</span><span v-if="q.marks!=null">{{q.marks}} {{q.marks===1?'mark':'marks'}}</span><span v-if="q.topic">{{q.topic}}</span></div>
    <details v-if="q.passage" class="bm-passage"><summary>Show passage</summary><QuestionContent lazy :text="q.passage" :images="[]"/></details>
    <QuestionContent lazy :text="q.text" :images="(q.images||[]).filter(x=>!x.option_key)"/>
    <div v-if="q.options?.length&&openOptions.has(q.id)" class="bm-options">
     <div v-for="(o,n) in q.options" :key="o.key" class="bm-option"><strong>{{letter(n)}}.</strong><QuestionContent lazy :text="o.text" :images="(q.images||[]).filter(x=>x.option_key===o.key)"/></div>
    </div>
    <div class="bm-actions">
     <button v-if="q.options?.length" type="button" class="btn btn-light btn-sm" :aria-expanded="openOptions.has(q.id)" @click="toggleOptions(q.id)"><ChevronDown :size="15" :class="{flip:openOptions.has(q.id)}"/>{{openOptions.has(q.id)?'Hide options':'Show options ('+q.options.length+')'}}</button>
     <a v-if="studyLink(q)" :href="studyLink(q)" class="btn btn-light btn-sm"><BookOpen :size="15"/>Open question</a>
     <a v-if="q.paper_id" :href="'/paper/'+q.paper_id" class="btn btn-light btn-sm"><ExternalLink :size="15"/>Paper</a>
     <span class="bm-spacer"></span>
     <button type="button" class="text-btn bm-remove" @click="remove(q)"><Trash2 :size="15"/>Remove</button>
    </div>
   </article>
  </section>
  <div v-if="filtered.length>limit" class="text-center my-3"><button type="button" class="btn btn-light" @click="limit+=30">Show more ({{filtered.length-limit}} left)</button></div>
  <div class="bm-foot"><span class="muted small">Bookmarks are saved on this device only. Clearing browser data removes them.</span><button type="button" class="text-btn bm-remove" @click="clearAll">Remove all</button></div>
 </template>

 <div v-if="undo" class="bm-toast" role="status"><span>{{undo.label}}</span><button type="button" @click="undoRemove">Undo</button></div>
</div>
</template>
<style scoped>
.bm-head{align-items:flex-end;margin-bottom:18px}.bm-head h1{margin-bottom:4px}
.bm-head .btn,.bm-group-head .btn{display:inline-flex;align-items:center;gap:6px}
.bm-empty{display:flex;flex-direction:column;align-items:center;gap:8px}.bm-empty svg{color:var(--blue)}
.bm-toolbar{display:grid;grid-template-columns:minmax(0,1fr) 220px 170px;gap:10px;padding:14px;margin-bottom:22px}
.bm-search{position:relative;margin:0}.bm-search svg{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#8c9bb0}.bm-search input{padding-left:40px}
.bm-group{margin-bottom:26px}
.bm-group-head{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:0 2px 10px}
.bm-group-head h2{font-size:1.02rem;margin:0}.bm-group-head .muted{font-size:.8rem}
.bm-card{padding:18px 20px;margin-bottom:12px}
.bm-meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.bm-meta span{font-size:.72rem;font-weight:650;color:#5a6d87;background:#f2f5fa;border:1px solid #e7ecf3;border-radius:999px;padding:3px 9px}
.bm-meta .bm-qno{background:#edf3ff;color:#2856b6;border-color:#d6e2fb}
.bm-passage{margin-bottom:10px;font-size:.92rem}.bm-passage summary{cursor:pointer;color:var(--blue);font-weight:600;font-size:.84rem}
.bm-options{display:grid;gap:8px;margin-top:12px}
.bm-option{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:.93rem}
.bm-actions{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}
.bm-actions .btn{display:inline-flex;align-items:center;gap:6px}
.bm-actions .flip{transform:rotate(180deg)}
.bm-spacer{flex:1}
.bm-remove{color:#b54646;display:inline-flex;align-items:center;gap:5px;font-size:.84rem}
.bm-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:8px;flex-wrap:wrap}
.bm-toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:1100;display:flex;align-items:center;gap:16px;background:#172e54;color:#fff;padding:12px 16px 12px 20px;border-radius:10px;box-shadow:0 10px 30px #14233b40;font-size:.9rem}
.bm-toast button{background:none;border:0;color:#9cc0ff;font-weight:700;padding:2px 4px}
[data-theme="dark"] .bm-meta span{background:#1b2636;border-color:#2c3a4f;color:#bacce0}
[data-theme="dark"] .bm-meta .bm-qno{background:#22314a;color:#9cbbff;border-color:#2f4466}
@media(max-width:760px){
 .bm-toolbar{grid-template-columns:1fr 1fr}.bm-search{grid-column:1 / -1}
 .bm-head{flex-direction:column;align-items:flex-start;gap:10px}
 .bm-card{padding:14px}
 .bm-toast{bottom:calc(84px + env(safe-area-inset-bottom));width:calc(100% - 32px);justify-content:space-between}
}
</style>
