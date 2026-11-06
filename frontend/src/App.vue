<script setup>
import {ref,onMounted,onUnmounted,computed,defineAsyncComponent} from 'vue';
import {BookOpen,LayoutDashboard,History,Bookmark,Target,ShieldCheck,Search,ArrowUpRight,GraduationCap,LogOut,MessageSquare} from 'lucide-vue-next';
import {api,session,loadSession,loadHome,go} from './api';
const About=defineAsyncComponent(()=>import('./About.vue'));
import Catalog from './Catalog.vue';
const ExamBrowser=defineAsyncComponent(()=>import('./ExamBrowser.vue'));
const Exam=defineAsyncComponent(()=>import('./Exam.vue'));
const Records=defineAsyncComponent(()=>import('./Records.vue'));
const Admin=defineAsyncComponent(()=>import('./Admin.vue'));
const theme=ref(localStorage.getItem('pyq-theme')||(window.matchMedia?.('(prefers-color-scheme: dark)').matches?'dark':'light'));
document.documentElement.dataset.theme=theme.value;document.documentElement.dataset.bsTheme=theme.value;
function toggleTheme(){theme.value=theme.value==='dark'?'light':'dark';document.documentElement.dataset.theme=theme.value;document.documentElement.dataset.bsTheme=theme.value;localStorage.setItem('pyq-theme',theme.value)}
import {currentRoute,migrateLegacyRoute,installNavigation} from './navigation';
migrateLegacyRoute();
try{localStorage.removeItem('pyq-active-attempt')}catch{}
const route=ref(currentRoute());
const stopNavigation=installNavigation(path=>{route.value=path});onUnmounted(stopNavigation);
const busy=ref(route.value.startsWith('/admin')),error=ref(''),auth=ref({name:'',email:'',password:''}),authBusy=ref(false);
const examPage=computed(()=>route.value.startsWith('/attempt/'));
// The admin console has its own full-screen layout (sidebar, top bar, theme toggle).
const adminConsole=computed(()=>!busy.value&&route.value.startsWith('/admin')&&route.value!=='/admin/login'&&session.user?.role==='ADMIN');
onMounted(async()=>{if(!route.value.startsWith('/admin')&&!route.value.startsWith('/attempt/'))void loadHome().catch(()=>{});try{await loadSession()}catch(e){error.value=e.message}finally{busy.value=false}});
async function authenticate(){authBusy.value=true;error.value='';try{const d=await api('/auth/login',{method:'POST',body:auth.value});session.user=d.user;auth.value.password='';go('/admin')}catch(e){error.value=e.message}finally{authBusy.value=false}}
async function logout(){await api('/auth/logout',{method:'POST'});await loadSession();go('/')}
// [path, full label, icon, short label for the phone bottom bar]
const nav=[['/','Home',BookOpen,'Home'],['/progress','My progress',LayoutDashboard,'Progress'],['/bookmarks','Bookmarks',Bookmark,'Saved'],['/feedback','Site feedback',MessageSquare,'Feedback'],['/about','About MauryaHub',GraduationCap,'About']];
</script>
<template>
<Admin v-if="adminConsole"/>
<template v-else>
<button class="theme-toggle btn btn-light btn-sm" :class="{'exam-toggle':examPage}" @click="toggleTheme" :aria-label="'Switch to '+(theme==='dark'?'light':'dark')+' theme'"><span aria-hidden="true">{{theme==='dark'?'☀':'☾'}}</span><span class="theme-label">{{theme==='dark'?' Light':' Dark'}}</span></button>
<div class="app-shell" :class="{'exam-shell':examPage}">
<aside v-if="!examPage" class="sidebar"><a href="/" class="brand"><span class="brand-mark"><BookOpen :size="23"/></span><span>Maurya<span class="brand-light">Hub</span><small>PYQ PRACTICE</small></span></a><div class="nav-caption">YOUR WORKSPACE</div><nav><a v-for="[path,label,Icon,short] in nav" :href="path" :class="{active:route===path}" :aria-current="route===path?'page':undefined" ><component :is="Icon" :size="19" aria-hidden="true"/><span class="nav-full">{{label}}</span><span class="nav-short">{{short}}</span></a><a v-if="session.user?.role==='ADMIN'" href="/admin" :class="{active:route.startsWith('/admin')}"><ShieldCheck :size="19"/><span class="nav-full">Administration / Upload PYQ</span><span class="nav-short">Admin</span></a></nav><div class="sidebar-bottom"><a href="https://mauryahub.onrender.com/">← Back to MauryaHub</a></div></aside>
<div class="workspace"><header v-if="!examPage" class="topbar" :class="{'guest-topbar':session.user?.role!=='ADMIN'}"><span class="top-context">IITM BS <span>/</span> Previous-year papers</span><div class="account" v-if="session.user?.role==='ADMIN'"><span class="avatar">{{session.user.name.slice(0,1)}}</span><span>{{session.user.name}}</span><button @click="logout" aria-label="Log out" class="icon-btn"><LogOut :size="17"/></button></div></header>
<main :class="{'exam-main':examPage}"><p v-if="session.storageWarning" class="alert alert-warning" role="alert">{{session.storageWarning}}</p><div v-if="error" class="alert alert-danger" role="alert">{{error}}<button class="text-btn float-end" @click="error=''">Dismiss</button></div><p v-if="busy">Loading your workspace…</p>
<section v-else-if="['/admin/login','/login'].includes(route)" class="auth-panel panel"><div class="eyebrow">ADMINISTRATION</div><h1>Admin sign in</h1><p class="muted">Manage papers, source catalog and processing.</p><form @submit.prevent="authenticate"><label>Email<input class="form-control" type="email" v-model="auth.email" required autocomplete="username"></label><label>Password<input class="form-control" type="password" v-model="auth.password" required maxlength="128" autocomplete="current-password"></label><button class="btn btn-primary w-100 mt-4" :disabled="authBusy">{{authBusy?'Please wait…':'Sign in as admin'}}</button></form><a href="/" class="text-btn mt-4">Back to papers</a></section>
<section v-else-if="route.startsWith('/admin')&&session.user?.role!=='ADMIN'" class="empty panel"><h1>Administrator access</h1><a href="/admin/login" class="btn btn-primary">Admin sign in</a></section>
<Exam v-else-if="examPage" :id="Number(route.split('/')[2])" :key="route"/>
<About v-else-if="route==='/about'"/>
<Records v-else-if="['/progress','/history','/dashboard','/bookmarks','/mistakes','/feedback'].includes(route)||route.startsWith('/result/')" :route="route" :key="route"/>
<ExamBrowser v-else-if="route.startsWith('/exam/')" :route="route" :key="route"/><Catalog v-else :route="route" :key="route"/>
</main><footer v-if="!examPage" class="site-footer"><nav class="footer-links" aria-label="Site links"><a href="/study">Study library</a><a href="/contact">Contact</a><a href="/privacy">Privacy</a><a href="/content-policy">Content policy</a><a href="/about">About</a></nav><span class="footer-brand">MauryaHub · PYQ Practice</span></footer></div></div>
</template>
</template>
