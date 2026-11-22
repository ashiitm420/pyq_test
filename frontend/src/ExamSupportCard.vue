<script setup>
import { defineAsyncComponent, ref } from 'vue';

const emit = defineEmits(['dismiss']);
const checkoutOpen = ref(false);
const SupportCheckout = defineAsyncComponent(() => import('./SupportCheckout.vue'));
</script>

<template>
  <aside class="panel exam-support" aria-labelledby="exam-support-title">
    <div>
      <h2 id="exam-support-title">Help keep MauryaHub running</h2>
      <p class="muted">
        Keeping MauryaHub online comes with hosting and maintenance costs.
        If you found this practice exam helpful, please consider making a small
        contribution to help keep it free for everyone.
      </p>
    </div>
    <div class="d-flex flex-wrap align-items-center gap-2">
      <button type="button" class="btn btn-outline-primary" @click="checkoutOpen = true">
        Support MauryaHub
      </button>
      <button type="button" class="btn btn-light" @click="emit('dismiss')">Not now</button>
    </div>
  </aside>
  <SupportCheckout v-if="checkoutOpen" @close="checkoutOpen = false" />
</template>

<style scoped>
.exam-support {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: .75rem 1.25rem;
  margin-block: 1rem;
  padding: 1rem;
}

.exam-support h2 {
  margin: 0 0 .3rem;
  font-size: 1rem;
}

.exam-support p {
  max-width: 65ch;
  margin: 0;
  font-size: .875rem;
}
</style>
