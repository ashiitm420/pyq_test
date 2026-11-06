<script setup>
import {ref,defineAsyncComponent} from 'vue';
const open=ref(false);
const SupportCheckout=defineAsyncComponent(()=>import('./SupportCheckout.vue'));
</script>
<template><section class="panel support-entry"><h2>Support MauryaHub ☕</h2><p>MauryaHub stays free. If it helps your preparation, you can contribute towards hosting and maintenance. No login, subscription or extra access.</p><button type="button" class="btn btn-outline-primary" @click="open=true">Support MauryaHub ☕</button><SupportCheckout v-if="open" @close="open=false"/></section></template>
<style scoped>.support-entry{margin-top:24px}.support-entry h2{font-size:1.15rem}.support-entry p{color:var(--muted);max-width:70ch}</style>
