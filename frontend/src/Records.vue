<script setup>
import SavedAISolution from './SavedAISolution.vue';
import PaperProgress from './PaperProgress.vue';
import {ref,computed,onMounted,nextTick} from 'vue';import {api,session,go} from './api';import {answerText,clock} from './utils';import MathText from './MathText.vue';import QuestionContent from './QuestionContent.vue';import AnswerValue from './AnswerValue.vue';
const props=defineProps({route:String});const items=ref([]),total=ref(0),page=ref(1),error=ref(''),dashboard=ref(null),attempt=ref(null),showReview=ref(false),review=ref([]),reviewTotal=ref(0),reviewPage=ref(1);
const reviewLoading=ref(false),currentReview=ref(null),reviewCache=new Map(),allReview=ref([]),reviewFilter=ref('ALL'),viewMode=ref('all');let reviewVersion=0;
const fbItems=ref([]),fbTotal=ref(0),fbAvg=ref(0),fbCounts=ref({'5':0,'4':0,'3':0,'2':0,'1':0}),fbName=ref(''),fbStars=ref(5),fbText=ref(''),fbBusy=ref(false),fbMsg=ref(''),fbErr=ref('');
function resultState(p){return p.state?.startsWith('ANSWERED')?(p.outcome||'UNGRADED'):'SKIPPED'}
const result=props.route.startsWith('/result/'),collection=props.route==='/bookmarks',feedbackPage=props.route==='/feedback';
const hasFullReview=computed(()=>allReview.value.length>0);
const filterCounts=computed(()=>{
 const src=allReview.value.length?allReview.value:(attempt.value?.palette||[]).map(p=>({outcome:resultState(p)}));
 return {
  ALL:src.length,
  WRONG:src.filter(i=>['INCORRECT','PARTIAL'].includes(i.outcome)).length,
  CORRECT:src.filter(i=>i.outcome==='CORRECT').length,
  SKIPPED:src.filter(i=>!i.outcome||['SKIPPED','UNGRADED'].includes(i.outcome)).length,
 };
});
const visibleReview=computed(()=>{
 if(!hasFullReview.value)return review.value;
 let list=allReview.value;
 if(reviewFilter.value==='WRONG')list=list.filter(i=>['INCORRECT','PARTIAL'].includes(i.outcome));
 else if(reviewFilter.value==='CORRECT')list=list.filter(i=>i.outcome==='CORRECT');
 else if(reviewFilter.value==='SKIPPED')list=list.filter(i=>!i.outcome||['SKIPPED','UNGRADED'].includes(i.outcome));
 if(viewMode.value==='single'&&currentReview.value!==null){
  const match=list.find(i=>i.question.id===currentReview.value);
  return match?[match]:list.slice(0,1);
 }
 return list;
});
const currentSingleIndex=computed(()=>visibleReview.value.length&&currentReview.value!==null?allReview.value.findIndex(i=>i.question.id===currentReview.value):0);
function optionClass(q,ans,optKey){
 const isCorrect=Array.isArray(q.answers)&&q.answers.includes(optKey);
 const isChosen=Array.isArray(ans)&&ans.includes(optKey);
 return {'review-option-correct':isCorrect,'review-option-incorrect':isChosen&&!isCorrect,'review-option-chosen':isChosen};
}
function optionBadge(q,ans,optKey){
 const isCorrect=Array.isArray(q.answers)&&q.answers.includes(optKey);
 const isChosen=Array.isArray(ans)&&ans.includes(optKey);
 if(isCorrect&&isChosen)return '✓ Your answer · Correct';
 if(isCorrect)return '✓ Correct answer';
 if(isChosen)return '✗ Your answer';
 return '';
}
async function loadFeedback(){
 try{
  const d=await api('/feedback');
  fbItems.value=d.items||[];
  fbTotal.value=d.total||0;
  fbAvg.value=d.average_rating||0;
  if(d.rating_counts)fbCounts.value=d.rating_counts;
 }catch{}
}
async function submitFeedback(){
 if(fbBusy.value)return;
 fbErr.value='';fbMsg.value='';
 if(fbText.value.trim().length<3){fbErr.value='Please write at least a few words of feedback.';return}
 fbBusy.value=true;
 try{
  const d=await api('/feedback',{method:'POST',body:{name:fbName.value.trim(),stars:fbStars.value,message:fbText.value.trim()}});
  fbItems.value=d.items||[];
  fbTotal.value=d.total||0;
  fbAvg.value=d.average_rating||0;
  if(d.rating_counts)fbCounts.value=d.rating_counts;
  fbText.value='';
  fbMsg.value='Thank you! Your feedback has been published.';
 }catch(e){fbErr.value=e.message||'Could not submit feedback.'}
 finally{fbBusy.value=false}
}
function scrollToFeedback(){
 document.getElementById('result-feedback-section')?.scrollIntoView?.({behavior:'smooth',block:'start'});
}
async function load(){try{
 if(feedbackPage){
  await loadFeedback();
 }
 else if(result){
  attempt.value=await api('/attempts/'+props.route.split('/')[2]);
  if(attempt.value.status==='ACTIVE'){go('/attempt/'+attempt.value.id);return}
  if(Array.isArray(attempt.value.review_items)&&attempt.value.review_items.length){
   allReview.value=attempt.value.review_items;
   review.value=attempt.value.review_items;
   reviewTotal.value=attempt.value.review_items.length;
   showReview.value=true;
   currentReview.value=attempt.value.palette?.[0]?.question_id??attempt.value.review_items[0]?.question?.id??null;
  }
  void loadFeedback();
 }
 else if(collection){const d=await api('/bookmarks?page='+page.value);items.value=d.items;total.value=d.total}
 else{const d=await api('/progress?page='+page.value);items.value=d.items;total.value=d.total}
}catch(e){error.value=e.message}}
onMounted(load);
async function practice(paper_id){try{const a=await api('/attempts',{method:'POST',body:collection?{collection:props.route.slice(1),mode:'practice'}:{paper_id,mode:'practice'}});go('/attempt/'+a.id)}catch(e){error.value=e.message}}
async function practiceWrong(){try{const a=await api('/attempts',{method:'POST',body:{collection:'mistakes',attempt_id:attempt.value.id,mode:'practice'}});go('/attempt/'+a.id)}catch(e){error.value=e.message}}
async function getReview(target=null){const generation=++reviewVersion;reviewLoading.value=true;error.value='';try{const cachedItem=reviewCache.get(reviewPage.value);const d=cachedItem?{items:[cachedItem],total:reviewTotal.value}:await api('/attempts/'+attempt.value.id+'/review?page='+reviewPage.value+'&limit=1');if(generation!==reviewVersion)return;if(d.items?.[0])reviewCache.set(reviewPage.value,d.items[0]);review.value=d.items;reviewTotal.value=d.total;showReview.value=true;await nextTick();if(target!==null)document.getElementById('review-question-'+target)?.scrollIntoView?.({behavior:'smooth',block:'start'})}catch(e){if(generation===reviewVersion)error.value=e.message}finally{if(generation===reviewVersion)reviewLoading.value=false}}
async function jumpReview(p,n){
 currentReview.value=p.question_id;
 if(hasFullReview.value){
  showReview.value=true;
  if(reviewFilter.value!=='ALL'&&!visibleReview.value.some(i=>i.question.id===p.question_id))reviewFilter.value='ALL';
  await nextTick();
  document.getElementById('review-question-'+p.question_id)?.scrollIntoView?.({behavior:'smooth',block:'start'});
  return;
 }
 const targetPage=(p.review_index??n)+1;
 if(showReview.value&&reviewPage.value===targetPage&&review.value.some(i=>i.question.id===p.question_id)){await nextTick();document.getElementById('review-question-'+p.question_id)?.scrollIntoView?.({behavior:'smooth',block:'start'});return}
 reviewPage.value=targetPage;review.value=[];await getReview(p.question_id);
}
function setFilter(f){
 reviewFilter.value=f;
 if(viewMode.value==='single'){
  const first=visibleReview.value[0];
  if(first)currentReview.value=first.question.id;
 }
}
async function stepSingle(delta){
 const idx=currentSingleIndex.value+delta;
 if(idx>=0&&idx<allReview.value.length){
  reviewFilter.value='ALL';
  currentReview.value=allReview.value[idx].question.id;
  await nextTick();
  document.getElementById('review-question-'+currentReview.value)?.scrollIntoView?.({behavior:'smooth',block:'start'});
 }
}
function scrollToPalette(){
 document.querySelector('.result-panel')?.scrollIntoView?.({behavior:'smooth',block:'start'});
}
async function remove(id){await api('/questions/'+id+'/bookmark',{method:'DELETE'});await load()}
</script>
<template><div v-if="error" class="alert alert-danger">{{error}}</div>
<template v-if="feedbackPage">
<div class="eyebrow">COMMUNITY REVIEWS</div>
<div class="section-row"><h1>MauryaHub Site Feedback</h1></div>
<p class="muted">Share your experience using MauryaHub PYQ Practice and read real feedback from fellow students.</p>
<div class="panel feedback-summary-bar mt-3">
 <div class="feedback-avg-box">
  <span class="eyebrow">OVERALL RATING</span>
  <strong>{{fbTotal?fbAvg+' / 5':'—'}}</strong>
  <span class="feedback-stars-static">{{'★'.repeat(Math.round(fbAvg||5))}}{{'☆'.repeat(5-Math.round(fbAvg||5))}}</span>
  <small class="muted">{{fbTotal?fbTotal+' verified student '+(fbTotal===1?'review':'reviews'):'No reviews yet · Be the first!'}}</small>
 </div>
 <div class="feedback-form-box">
  <h2 class="h5 mb-2">Share your feedback</h2>
  <form @submit.prevent="submitFeedback" class="feedback-form">
   <div class="feedback-form-row">
    <label class="feedback-label">1. Your name <small class="muted">(optional)</small><input class="form-control" type="text" maxlength="80" placeholder="Anonymous Student" :value="fbName" @input="fbName=$event.target.value"></label>
    <div class="feedback-label"><span>2. Rating <small class="muted">(out of 5)</small></span><div class="feedback-stars-picker" role="radiogroup" aria-label="Star rating out of 5"><button v-for="st in [1,2,3,4,5]" :key="st" type="button" class="star-pick-btn" :class="{active:st<=fbStars}" :aria-label="st+' out of 5 stars'" @click="fbStars=st">★</button><span class="star-pick-count">{{fbStars}} / 5</span></div></div>
   </div>
   <label class="feedback-label mt-2">3. Your feedback about MauryaHub<textarea class="form-control" rows="3" maxlength="1500" placeholder="Tell us what you like about the site or what feature we should improve next…" :value="fbText" @input="fbText=$event.target.value" required></textarea></label>
   <p v-if="fbErr" class="alert alert-danger mt-2 mb-0" role="alert">{{fbErr}}</p>
   <p v-if="fbMsg" class="alert alert-success mt-2 mb-0" role="status">{{fbMsg}}</p>
   <div class="mt-3"><button type="submit" class="btn btn-primary" :disabled="fbBusy">{{fbBusy?'Posting…':'Post feedback'}}</button></div>
  </form>
 </div>
</div>
<section class="mt-4">
 <div class="section-row"><h2 class="h4 mb-0">Student Feedbacks ({{fbTotal}})</h2></div>
 <div v-if="!fbItems.length" class="empty panel mt-3"><h3>No student feedbacks yet.</h3><p class="muted mb-0">Submit the form above to share the first review of MauryaHub!</p></div>
 <div v-else class="feedback-wall-grid mt-3">
  <article v-for="item in fbItems" :key="item.id" class="panel feedback-item-card">
   <div class="feedback-item-head">
    <div class="feedback-author"><span class="feedback-avatar">{{(item.name||'A').slice(0,1).toUpperCase()}}</span><div><strong>{{item.name}}</strong><small class="muted d-block">{{new Date(item.created_at*1000).toLocaleDateString()}}</small></div></div>
    <span class="feedback-item-stars" :aria-label="item.stars+' out of 5 stars'">{{'★'.repeat(item.stars)}}{{'☆'.repeat(5-item.stars)}}</span>
   </div>
   <p class="feedback-item-text mb-0">{{item.message}}</p>
  </article>
 </div>
</section>
</template>
<template v-else-if="result&&attempt"><div class="eyebrow">ATTEMPT COMPLETE</div><h1>Your results</h1><p class="muted">{{attempt.title}}</p><p class="notice">Results and question review are temporary, available until {{new Date(attempt.expires_at*1000).toLocaleString()}}. Only your latest paper percentage is saved in this browser.</p><p v-if="attempt.records_progress===false" class="muted">This targeted practice does not replace your full-paper score.</p><div class="result-panel panel" v-if="attempt.result"><div class="result-score"><span class="eyebrow">{{attempt.result.pending_manual?'PROVISIONAL SCORE':'YOUR SCORE'}}</span><strong>{{attempt.result.score}}<small> / {{attempt.result.total_marks??'—'}}</small></strong><span>{{attempt.result.percentage===null?'Percentage unavailable':attempt.result.percentage+'%'}}</span></div><div class="result-question-summary"><div class="result-stats-strip"><div class="stat-pill"><span>Attempted</span><strong>{{attempt.result.attempted??0}} / {{attempt.palette?.length||0}}</strong></div><div class="stat-pill stat-pill-green"><span>Correct</span><strong>{{attempt.result.correct??0}}</strong></div><div class="stat-pill stat-pill-red"><span>Incorrect</span><strong>{{attempt.result.incorrect??0}}</strong></div><div v-if="attempt.result.partial" class="stat-pill stat-pill-amber"><span>Partial</span><strong>{{attempt.result.partial}}</strong></div><div class="stat-pill"><span>Accuracy</span><strong>{{attempt.result.accuracy!=null?attempt.result.accuracy+'%':'—'}}</strong></div><div class="stat-pill"><span>Time taken</span><strong>{{clock(attempt.result?.time_taken||0)}}</strong></div></div><h2>Question review <small class="muted fw-normal fs-6">— click any number to jump directly</small></h2><div class="result-question-palette" aria-label="Result question palette"><button v-for="(p,n) in attempt.palette" :key="p.question_id" type="button" :class="['result-'+resultState(p).toLowerCase(),{current:currentReview===p.question_id}]" :aria-label="'Review question '+p.number+', '+resultState(p).toLowerCase()" :aria-current="currentReview===p.question_id?'step':undefined" @click="jumpReview(p,n)">{{p.number}}</button></div><div class="result-palette-legend"><span>🟩 Correct</span><span>🟥 Incorrect</span><span class="partial-label">▣ Partial</span><span>□ Not attempted</span><span>▧ Ungraded</span></div><p v-if="reviewLoading" role="status">Loading question review…</p></div></div><p v-if="attempt.result?.pending_manual" class="alert alert-warning">Some responses have no reliable source key/marks or cannot be automatically graded. The score is provisional.</p><p class="muted">Time taken: {{clock(attempt.result?.time_taken||0)}} · Negative marks: {{attempt.result?.negative_marks}}</p><div class="d-flex gap-3 flex-wrap"><button v-if="(attempt.result?.incorrect||0)+(attempt.result?.partial||0)>0" class="btn btn-outline-primary" @click="practiceWrong">Practice incomplete / wrong answers ({{(attempt.result.incorrect||0)+(attempt.result.partial||0)}})</button><button v-if="attempt.paper_id" class="btn btn-outline-primary" @click="practice(attempt.paper_id)">Practice again</button><button type="button" class="btn btn-outline-primary" @click="scrollToFeedback">★ Rate MauryaHub</button><a class="btn btn-light" :href="attempt.paper_id?'/paper/'+attempt.paper_id:'/progress'">Back to {{attempt.paper_id?'paper':'progress'}}</a></div>
<div v-if="hasFullReview" class="review-toolbar panel mt-4"><div class="review-filter-pills" role="tablist" aria-label="Filter questions by outcome"><button type="button" class="filter-pill" :class="{active:reviewFilter==='ALL'}" @click="setFilter('ALL')">All questions ({{filterCounts.ALL}})</button><button type="button" class="filter-pill filter-pill-wrong" :class="{active:reviewFilter==='WRONG'}" @click="setFilter('WRONG')">Incorrect / Partial ({{filterCounts.WRONG}})</button><button type="button" class="filter-pill filter-pill-correct" :class="{active:reviewFilter==='CORRECT'}" @click="setFilter('CORRECT')">Correct ({{filterCounts.CORRECT}})</button><button type="button" class="filter-pill" :class="{active:reviewFilter==='SKIPPED'}" @click="setFilter('SKIPPED')">Not attempted ({{filterCounts.SKIPPED}})</button></div><div class="review-mode-toggle"><button type="button" class="btn btn-sm" :class="viewMode==='all'?'btn-primary':'btn-light'" @click="viewMode='all'">Scroll all</button><button type="button" class="btn btn-sm" :class="viewMode==='single'?'btn-primary':'btn-light'" @click="viewMode='single'">One by one</button></div></div>
<section v-if="showReview" class="mt-3"><p v-if="hasFullReview&&!visibleReview.length" class="empty panel">No questions in this filter. <button type="button" class="text-btn" @click="setFilter('ALL')">Show all questions</button></p><article v-for="i in visibleReview" :key="i.question.id" :id="'review-question-'+i.question.id" class="panel review-card" :class="'review-'+String(i.outcome||'UNGRADED').toLowerCase()"><div class="section-row"><div><span class="eyebrow">{{i.question.kind?.replace('_',' / ')}} · {{i.question.marks!=null?i.question.marks+' marks':'Marks not specified'}}</span><h3 class="mb-0">Question {{i.question.number}}</h3></div><div class="d-flex align-items-center gap-2 flex-wrap"><span class="status review-outcome">{{i.outcome==='CORRECT'?'Correct':i.outcome==='PARTIAL'?'Partially correct':i.outcome==='INCORRECT'?'Incorrect':i.outcome==='SKIPPED'?'Not attempted':'Ungraded'}} · {{i.awarded??'—'}} marks</span><button v-if="hasFullReview&&viewMode==='all'" type="button" class="btn btn-light btn-sm" @click="scrollToPalette">↑ Palette</button></div></div><QuestionContent lazy :text="[i.question.passage,i.question.text].filter(Boolean).join('\n\n')" :images="(i.question.images||[]).filter(x=>!x.option_key)"/><div v-for="(o,oi) in i.question.options" :key="o.key" class="review-option" :class="optionClass(i.question,i.answer,o.key)"><strong>{{String.fromCharCode(65+oi)}}.</strong><div class="review-option-body"><QuestionContent lazy :text="o.text" :images="(i.question.images||[]).filter(x=>x.option_key===o.key)"/></div><span v-if="optionBadge(i.question,i.answer,o.key)" class="review-option-badge">{{optionBadge(i.question,i.answer,o.key)}}</span></div><div class="answer-comparison"><div><span>Your answer</span><AnswerValue :question="i.question" :value="i.answer" empty="Not answered"/></div><div><span>Correct answer</span><AnswerValue :question="i.question" :value="i.question.answers"/></div></div><MathText v-if="i.question.explanation" :text="i.question.explanation"/><SavedAISolution :attempt-id="attempt.id" :question-id="i.question.id" :saved="i.ai_solution"/><p v-if="i.manual_note">Reviewer: {{i.manual_note}}</p><div v-if="hasFullReview&&viewMode==='single'" class="d-flex justify-content-between mt-3 pt-3 border-top"><button type="button" class="btn btn-light" :disabled="currentSingleIndex<=0" @click="stepSingle(-1)">← Previous question</button><button type="button" class="btn btn-primary" :disabled="currentSingleIndex>=allReview.length-1" @click="stepSingle(1)">Next question →</button></div></article></section>
<section id="result-feedback-section" class="panel feedback-result-card mt-4">
 <div class="section-row">
  <div><span class="eyebrow">SITE FEEDBACK</span><h2 class="h4 mb-1">Enjoying MauryaHub? Share your feedback</h2><p class="muted mb-0">Your review helps us improve the site for all students.</p></div>
  <a href="/feedback" class="btn btn-light btn-sm">View all feedbacks ({{fbTotal}}) →</a>
 </div>
 <form @submit.prevent="submitFeedback" class="feedback-form mt-3">
  <div class="feedback-form-row">
   <label class="feedback-label">1. Your name <small class="muted">(optional)</small><input class="form-control" type="text" maxlength="80" placeholder="Anonymous Student" :value="fbName" @input="fbName=$event.target.value"></label>
   <div class="feedback-label"><span>2. Rating <small class="muted">(out of 5)</small></span><div class="feedback-stars-picker" role="radiogroup" aria-label="Star rating out of 5"><button v-for="st in [1,2,3,4,5]" :key="st" type="button" class="star-pick-btn" :class="{active:st<=fbStars}" :aria-label="st+' out of 5 stars'" @click="fbStars=st">★</button><span class="star-pick-count">{{fbStars}} / 5</span></div></div>
  </div>
  <label class="feedback-label mt-2">3. Your feedback about MauryaHub<textarea class="form-control" rows="2" maxlength="1500" placeholder="Share what you like about the site or what we can improve…" :value="fbText" @input="fbText=$event.target.value" required></textarea></label>
  <p v-if="fbErr" class="alert alert-danger mt-2 mb-0" role="alert">{{fbErr}}</p>
  <p v-if="fbMsg" class="alert alert-success mt-2 mb-0" role="status">{{fbMsg}} <a href="/feedback" class="fw-semibold ms-1">See all student feedbacks →</a></p>
  <div class="mt-3"><button type="submit" class="btn btn-primary" :disabled="fbBusy">{{fbBusy?'Posting…':'Post feedback'}}</button></div>
 </form>
</section>
</template>
<section v-else-if="result" class="empty panel"><p v-if="!error">Loading result…</p><p v-else>Open My progress to see your latest paper score or retake a paper.</p><a class="btn btn-primary" href="/progress">My progress</a></section>
<template v-else>
<div class="eyebrow">YOUR PRACTICE WORKSPACE</div>
<div class="section-row"><h1>{{collection?'My bookmarks':'My progress'}}</h1><button v-if="collection&&items.length" class="btn btn-primary" @click="practice()">Practice bookmarks</button></div>
<p v-if="!collection" class="muted">One latest score per paper. Retaking a paper replaces its previous score; scores and bookmarks stay on this browser only. Clearing site data removes them.</p>
<div v-if="!items.length" class="empty panel"><h3>{{collection?'No bookmarks yet.':'No completed papers yet.'}}</h3><a href="/" class="btn btn-primary">Explore courses</a></div>
<template v-else-if="collection"><article class="panel review-card" v-for="q in items" :key="q.id"><span class="eyebrow">{{q.kind}} · {{q.topic||'Topic not specified'}}</span><QuestionContent :text="q.text" :images="(q.images||[]).filter(x=>!x.option_key)"/><div class="d-flex gap-2 mt-3"><a :href="'/paper/'+q.paper_id" class="btn btn-light">Open paper</a><button class="text-btn" @click="remove(q.id)">Remove bookmark</button></div></article></template>
<template v-else><article v-for="p in items" :key="p.paper_id" class="paper-row panel"><div class="paper-info"><span class="eyebrow">{{p.course}} · {{p.exam}} · {{p.term}}</span><h3>{{p.name}}</h3><PaperProgress :progress="p"/></div><a class="btn btn-primary" :href="'/paper/'+p.paper_id">Retake Test</a></article></template>
<div v-if="total>24" class="pagination-row"><button class="btn btn-light" :disabled="page===1" @click="page--;load()">Previous</button><span>Page {{page}}</span><button class="btn btn-light" :disabled="page*24>=total" @click="page++;load()">Next</button></div>
</template></template>
