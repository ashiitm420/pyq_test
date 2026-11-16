<script setup>
import {ref,onMounted,onUnmounted} from 'vue';
import {Users,TrendingUp,CheckCircle2,BookOpen} from 'lucide-vue-next';
import {quizRecap as recap} from './quizRecap';
// Rounded DOWN from the recorded snapshot; animation never invents activity.
const metrics=[{label:'Learner reach*',value:Math.floor(recap.browsers/100)*100,icon:Users},{label:'Practice sessions started',value:Math.floor(recap.starts/100)*100,icon:TrendingUp},{label:'Tests completed',value:Math.floor(recap.completed/100)*100,icon:CheckCircle2},{label:'Papers practised',value:Math.floor(recap.papers/100)*100,icon:BookOpen}];
const root=ref(null),values=ref(metrics.map(m=>m.value)),progress=ref(1);let observer,frame,started=false;
function animate(){
 if(started)return;started=true;observer?.disconnect();
 if(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return;
 values.value=metrics.map(()=>0);progress.value=0;let first;
 function tick(now){first??=now;const p=Math.min(1,(now-first)/850),eased=1-(1-p)**3;values.value=metrics.map(m=>Math.floor(m.value*eased));progress.value=eased;if(p<1)frame=requestAnimationFrame(tick)}
 frame=requestAnimationFrame(tick);
}
onMounted(()=>{if(typeof IntersectionObserver==='undefined')return;observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting))animate()},{threshold:.2});observer.observe(root.value)});
onUnmounted(()=>{observer?.disconnect();if(frame)cancelAnimationFrame(frame)});
</script>
<template><section ref="root" class="quiz-recap" aria-labelledby="reach-title"><div class="recap-heading"><div><span class="eyebrow">MAURYAHUB IN NUMBERS</span><h2 id="reach-title">More practice. More confidence.</h2><p class="muted">A growing community, preparing together.</p></div><span class="recap-date">Updated {{recap.updated}}</span></div><div class="recap-grid"><div v-for="(m,n) in metrics" :key="m.label" class="reach-metric"><component :is="m.icon" :size="22" aria-hidden="true"/><strong :aria-label="m.value.toLocaleString('en-IN')+' plus'"><span aria-hidden="true">{{values[n].toLocaleString('en-IN')}}<small>+</small></span></strong><span>{{m.label}}</span><div class="metric-track" aria-hidden="true"><i :style="{transform:'scaleX('+progress+')'}"/></div></div></div><p class="recap-note">Across MauryaHub practice and exams · *Reach estimated from participating browsers. Recorded through {{recap.through}}.</p></section></template>
<style scoped>
.quiz-recap{margin:24px 0 12px;padding:28px;border:1px solid var(--line,#dce4ef);border-radius:18px;background:var(--panel,#fff)}.recap-heading{display:flex;justify-content:space-between;align-items:center;gap:16px}.recap-heading h2{font-size:1.5rem;margin:8px 0}.recap-heading p{margin:0;font-size:.9rem}.recap-date{color:var(--muted,#64748b);font-size:.75rem;white-space:nowrap}.recap-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin:24px 0}.reach-metric{background:color-mix(in srgb,var(--panel,#fff),#168575 5%);border-radius:12px;padding:18px;color:#258f80}.reach-metric strong{display:block;margin-top:12px;font-size:2.3rem;line-height:1.3;color:var(--text,#173555);font-variant-numeric:tabular-nums}.reach-metric strong small{font-size:1.4rem;margin-left:3px;color:#258f80}.reach-metric>span{font-size:.86rem;color:var(--muted,#64748b)}.metric-track{height:3px;background:#16857518;border-radius:8px;margin-top:18px;overflow:hidden}.metric-track i{display:block;height:100%;background:#258f80;transform-origin:left}.recap-note{margin:0;font-size:.72rem;color:var(--muted,#64748b)}@media(max-width:700px){.quiz-recap{padding:20px}.recap-heading{align-items:start;flex-direction:column;gap:10px}.recap-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.reach-metric{padding:14px}.reach-metric strong{font-size:1.8rem}}
</style>
