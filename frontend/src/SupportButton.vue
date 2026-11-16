<script setup>
import {ref,defineAsyncComponent} from 'vue';
const open=ref(false);const SupportCheckout=defineAsyncComponent(()=>import('./SupportCheckout.vue'));
</script>
<template><div><button type="button" class="btn support-button" @click="open=true">☕ Support us</button><SupportCheckout v-if="open" @close="open=false"/></div></template>
<style scoped>.support-button{border:1px solid #1b8878;background:#177e70;color:white;font-weight:700;padding:12px 20px;border-radius:12px;white-space:nowrap}.support-button:hover{background:#10685c;color:white}.support-button:focus-visible{outline:3px solid #4dbdaf;outline-offset:3px}</style>
