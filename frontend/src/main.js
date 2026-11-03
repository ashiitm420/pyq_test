import {createApp} from 'vue';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'katex/dist/katex.min.css';
import './style.css';
import './features.css';
import App from './App.vue';
createApp(App).mount('#app');

if(typeof window!=='undefined'&&'serviceWorker' in navigator){window.addEventListener('load',()=>{navigator.serviceWorker.register('/sw.js').catch(()=>{})})}
