<script setup>
import {ref,computed,onMounted} from 'vue';
import {Linkedin,Instagram,Mail,GraduationCap,Timer,BookOpen,Bookmark,Sparkles,ArrowUpRight,ShieldCheck} from 'lucide-vue-next';
import {api,session} from './api';
import SupportEntry from './SupportEntry.vue';
const page=ref(null),draft=ref({}),editing=ref(false),busy=ref(false),loading=ref(true),error=ref(''),message=ref(''),version=ref(Date.now());
async function load(){loading.value=true;error.value='';try{page.value=await api('/about')}catch(e){error.value=e.message}finally{loading.value=false}}onMounted(load);
function edit(){draft.value=Object.fromEntries(['headline','description','name','bio','contact_email'].map(k=>[k,page.value[k]]));editing.value=true;message.value=''}
async function save(){busy.value=true;error.value='';message.value='';try{page.value=await api('/admin/about',{method:'PUT',body:draft.value});editing.value=false;message.value='About page saved.'}catch(e){error.value=e.message}finally{busy.value=false}}
async function photo(e){const f=e.target.files?.[0];if(!f)return;if(f.size>5*1024*1024){error.value='Photo must be 5 MB or smaller.';e.target.value='';return}const form=new FormData();form.append('photo',f);await changePhoto('POST',form);e.target.value=''}
async function changePhoto(method,form){busy.value=true;error.value='';message.value='';try{page.value=await api('/admin/about/photo',{method,form});version.value=Date.now();message.value=method==='DELETE'?'Photo removed.':'Photo updated.'}catch(e){error.value=e.message}finally{busy.value=false}}
// Public profile links. Change them here; no server change is needed.
const SOCIAL={linkedin:'https://www.linkedin.com/in/ashish-raj-02a700259/',instagram:'https://www.instagram.com/ashraj7777/',instagramHandle:'@ashraj7777'};
const initials=computed(()=>(page.value?.name||'MauryaHub').split(/\s+/).filter(Boolean).slice(0,2).map(w=>w[0].toUpperCase()).join(''));
const features=[
 {icon:BookOpen,title:'Practice mode',text:'Answer at your own pace and check each answer instantly.'},
 {icon:Timer,title:'Exam mode',text:'Timed attempts in a familiar computer-based exam layout.'},
 {icon:Sparkles,title:'Explained solutions',text:'Step-by-step explanations after you attempt a question.'},
 {icon:Bookmark,title:'Bookmarks & progress',text:'Save questions and track your latest score in your browser.'},
 {icon:ShieldCheck,title:'Free, no login',text:'Open a paper and start. No account or payment needed.'},
];
</script>
<template>
<section class="about-page" :aria-busy="busy||loading">
<div class="eyebrow">ABOUT MAURYAHUB</div>
<p v-if="error" class="alert alert-danger" role="alert">{{error}} <button v-if="!page&&!loading" class="text-btn" @click="load">Retry</button></p>
<p v-if="message" class="alert alert-success" role="status">{{message}}</p><p v-if="loading" role="status">Loading About…</p>
<template v-if="page">
<div class="section-row"><h1>MauryaHub <span class="muted">/ PYQ Practice</span></h1><button v-if="session.user?.role==='ADMIN'&&!editing" class="btn btn-primary" @click="edit">Edit About</button></div>

<form v-if="editing&&session.user?.role==='ADMIN'" class="panel about-editor" @submit.prevent="save"><h2>Edit About</h2><fieldset :disabled="busy">
<label>Headline<input class="form-control" v-model="draft.headline" maxlength="160" required></label>
<label>About this platform<textarea class="form-control" v-model="draft.description" maxlength="4000" rows="5" required></textarea></label>
<label>Public contact email<input class="form-control" type="email" v-model="draft.contact_email" maxlength="254" placeholder="For support and content removal requests"></label>
<label>Your name<input class="form-control" v-model="draft.name" maxlength="100" placeholder="Your public name"></label>
<label>Your introduction<textarea class="form-control" v-model="draft.bio" maxlength="2000" rows="4"></textarea></label>
<label>Profile photo<input class="form-control" type="file" accept="image/jpeg,image/png,image/webp" @change="photo"></label>
<p class="muted">JPG, PNG or WebP · up to 5 MB. Photo changes publish immediately; text publishes when you save.</p>
<button v-if="page.photo_url" class="btn btn-light" type="button" @click="changePhoto('DELETE')">Remove photo</button>
<div class="about-actions"><button class="btn btn-primary" type="submit">Save details</button><button class="btn btn-light" type="button" @click="editing=false">Cancel text changes</button></div></fieldset><p v-if="busy" role="status">Saving…</p></form>

<template v-else>
<!-- Creator profile -->
<section class="about-profile panel" aria-labelledby="creator-name">
 <div class="about-cover" aria-hidden="true"></div>
 <div class="about-profile-body">
  <div class="about-avatar">
   <img v-if="page.photo_url" :src="page.photo_url+'?v='+version" :alt="page.name||'MauryaHub creator'" width="132" height="132">
   <span v-else aria-hidden="true">{{initials}}</span>
  </div>
  <div class="about-profile-text">
   <div class="eyebrow">CREATOR OF MAURYAHUB</div>
   <h2 id="creator-name">{{page.name||'A student initiative'}}</h2>
   <p class="about-role"><GraduationCap :size="17" aria-hidden="true"/> Founder &amp; developer, MauryaHub</p>
   <p class="about-copy">{{page.bio}}</p>
   <nav class="about-social" aria-label="Connect with the creator">
    <a :href="SOCIAL.linkedin" target="_blank" rel="noopener noreferrer" class="social-btn linkedin"><Linkedin :size="17" aria-hidden="true"/>LinkedIn</a>
    <a :href="SOCIAL.instagram" target="_blank" rel="noopener noreferrer" class="social-btn instagram"><Instagram :size="17" aria-hidden="true"/>{{SOCIAL.instagramHandle}}</a>
    <a v-if="page.contact_email" :href="'mailto:'+page.contact_email" class="social-btn mail"><Mail :size="17" aria-hidden="true"/>Email</a>
   </nav>
  </div>
 </div>
</section>

<!-- Platform story -->
<article class="panel about-story"><h2>{{page.headline}}</h2><p class="about-copy">{{page.description}}</p><a class="btn btn-primary" href="/">Explore papers →</a></article>

<!-- What students get -->
<section class="about-features" aria-labelledby="features-title">
 <h2 id="features-title">What you get on MauryaHub</h2>
 <div class="feature-grid">
  <component :is="f.href?'a':'div'" v-for="f in features" :key="f.title" class="feature panel" v-bind="f.href?{href:f.href,target:'_blank',rel:'noopener noreferrer'}:{}">
   <span class="feature-icon"><component :is="f.icon" :size="19" aria-hidden="true"/></span>
   <strong>{{f.title}}<ArrowUpRight v-if="f.href" :size="14" aria-hidden="true" class="feature-ext"/></strong>
   <span>{{f.text}}</span>
  </component>
 </div>
</section>

<!-- Contact strip -->
<section class="about-contact panel">
 <div><h2>Questions, corrections or feedback?</h2><p class="muted mb-0">Found a formatting issue? Use <strong>Report Broken Format</strong> next to the question’s Bookmark button. For anything else, write to us.</p></div>
 <div class="about-contact-actions"><a class="btn btn-primary" href="/contact">Contact &amp; content removal</a><a class="btn btn-light" href="/feedback">Rate MauryaHub</a></div>
</section>

<p class="about-disclaimer">Independent student-built platform. Not affiliated with IIT Madras.</p>
<SupportEntry/>
</template>
</template></section>
</template>
<style scoped>
.about-page{max-width:1000px;margin:auto}
.about-page h1{font-size:clamp(1.6rem,4vw,2.3rem)}.about-page h1 span{font-weight:400}
.about-copy{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8}
.about-editor label{display:block;margin:18px 0}.about-editor input,.about-editor textarea{margin-top:8px}.about-editor fieldset{border:0;padding:0;min-width:0}
.about-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}
.about-editor,.about-story{padding:clamp(20px,4vw,40px);margin-top:26px}
.about-story h2{font-size:clamp(1.5rem,3.6vw,2.2rem);margin-bottom:16px}.about-story .btn{margin-top:10px}

/* Profile card */
.about-profile{padding:0;overflow:hidden;margin-top:22px}
.about-cover{height:120px;background:radial-gradient(circle at 85% 20%,#6d8fff 0,transparent 45%),linear-gradient(120deg,#172e54 0%,#285fd8 60%,#3f7bf0 100%)}
.about-profile-body{display:flex;gap:28px;padding:0 clamp(20px,4vw,40px) clamp(22px,4vw,36px)}
.about-avatar{flex:none;width:132px;height:132px;margin-top:-56px;border-radius:28px;border:5px solid var(--bs-body-bg,#fff);background:linear-gradient(135deg,#285fd8,#6d8fff);display:grid;place-items:center;overflow:hidden;box-shadow:0 10px 28px #14233b33}
.about-avatar img{width:100%;height:100%;object-fit:cover}
.about-avatar span{color:#fff;font-size:2.6rem;font-weight:800;letter-spacing:-.02em}
.about-profile-text{padding-top:20px;min-width:0}
.about-profile-text h2{font-size:clamp(1.5rem,3.4vw,2rem);margin:2px 0 6px}
.about-role{display:flex;align-items:center;gap:7px;color:var(--muted);font-weight:600;font-size:.92rem;margin-bottom:12px}
.about-social{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}
.social-btn{display:inline-flex;align-items:center;gap:8px;padding:9px 15px;border-radius:999px;font-weight:650;font-size:.88rem;border:1px solid transparent;color:#fff;transition:transform .15s,box-shadow .15s}
.social-btn:hover{transform:translateY(-1px);box-shadow:0 6px 16px #14233b26;color:#fff}
.social-btn.linkedin{background:#0a66c2}
.social-btn.instagram{background:linear-gradient(45deg,#f58529,#dd2a7b 50%,#8134af)}
.social-btn.mail{background:transparent;color:var(--blue);border-color:#c7d7ef}
.social-btn.mail:hover{color:var(--blue);background:#edf3ff}

/* Features */
.about-features{margin-top:30px}.about-features h2{font-size:1.3rem;margin-bottom:14px}
.feature-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.feature{display:flex;flex-direction:column;gap:6px;padding:18px;color:inherit;margin:0}
a.feature{transition:border-color .15s,box-shadow .15s}a.feature:hover{border-color:#a9bfec;box-shadow:0 8px 22px #18396912}
.feature-icon{display:grid;place-items:center;width:38px;height:38px;border-radius:10px;background:#edf3ff;color:#285fd8;margin-bottom:4px}
.feature strong{display:flex;align-items:center;gap:5px;font-size:.98rem}.feature-ext{color:var(--muted)}
.feature>span:last-child{color:var(--muted);font-size:.88rem;line-height:1.55}

/* Contact */
.about-contact{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-top:30px;padding:24px 28px}
.about-contact h2{font-size:1.15rem;margin-bottom:6px}
.about-contact-actions{display:flex;gap:10px;flex-wrap:wrap;flex:none}
.about-disclaimer{margin:22px 0 0;color:var(--muted);font-size:.85rem;text-align:center}

[data-theme="dark"] .feature-icon{background:#22314a;color:#9cbbff}
[data-theme="dark"] .social-btn.mail{border-color:#435064;color:#9cbbff}
[data-theme="dark"] .about-avatar{border-color:#1a2435}

@media(max-width:860px){.feature-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){
 .about-profile-body{flex-direction:column;gap:6px}
 .about-avatar{width:108px;height:108px;margin-top:-50px;border-radius:24px}.about-avatar span{font-size:2.1rem}
 .about-profile-text{padding-top:8px}
 .feature-grid{grid-template-columns:1fr}
 .about-contact{flex-direction:column;align-items:flex-start}
 .section-row{align-items:flex-start;gap:15px;flex-wrap:wrap}
}
@media(prefers-reduced-motion:reduce){.social-btn{transition:none}.social-btn:hover{transform:none}}
</style>
