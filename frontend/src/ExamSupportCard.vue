<script setup>
import { defineAsyncComponent, onMounted, ref } from 'vue';

const emit = defineEmits(['dismiss']);
const dialog = ref(null);
const checkoutOpen = ref(false);
const SupportCheckout = defineAsyncComponent(() => import('./SupportCheckout.vue'));

onMounted(() => dialog.value.showModal());

function dismiss() {
  dialog.value.close();
  emit('dismiss');
}

function openCheckout() {
  dialog.value.close();
  checkoutOpen.value = true;
}
</script>

<template>
  <dialog
    v-if="!checkoutOpen"
    ref="dialog"
    class="exam-support"
    aria-labelledby="exam-support-title"
    aria-describedby="exam-support-description"
    @cancel.prevent="dismiss"
    @click.self="dismiss"
  >
    <div class="exam-support-content">
      <button type="button" class="exam-support-close" aria-label="Close support prompt" @click="dismiss">×</button>
      <h2 id="exam-support-title">Help keep MauryaHub running</h2>
      <p id="exam-support-description">
        Keeping MauryaHub online comes with hosting and maintenance costs.
        If you found this practice exam helpful, please consider making a small
        contribution to help keep it free for everyone.
      </p>
      <div class="exam-support-actions">
        <button type="button" class="btn btn-light" autofocus @click="dismiss">Not now</button>
        <button type="button" class="btn btn-primary" @click="openCheckout">Support MauryaHub</button>
      </div>
    </div>
  </dialog>
  <SupportCheckout v-else @close="emit('dismiss')" />
</template>

<style scoped>
.exam-support {
  --prompt-surface: #fff;
  --prompt-ink: #172943;
  --prompt-muted: #576b86;
  --prompt-border: #dbe3ef;
  width: min(30rem, calc(100% - 2rem));
  max-height: calc(100dvh - 2rem);
  margin: auto;
  padding: 0;
  border: 1px solid var(--prompt-border);
  border-radius: 14px;
  color: var(--prompt-ink);
  background: var(--prompt-surface);
  box-shadow: 0 18px 60px #101e3a40;
}

.exam-support::backdrop {
  background: #101a2a99;
}

:global([data-theme="dark"] .exam-support) {
  --prompt-surface: #1e2938;
  --prompt-ink: #edf3fc;
  --prompt-muted: #b9c9dd;
  --prompt-border: #526479;
}

.exam-support-content {
  position: relative;
  padding: clamp(1.125rem, 5vw, 1.75rem);
}

.exam-support h2 {
  margin: 0 .9rem .75rem 0;
  color: var(--prompt-ink);
  font-size: 1.25rem;
  line-height: 1.3;
}

.exam-support p {
  margin: 0;
  color: var(--prompt-muted);
  line-height: 1.6;
}

.exam-support-close {
  position: absolute;
  top: .5rem;
  right: .625rem;
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 0;
  border-radius: 6px;
  color: var(--prompt-muted);
  background: transparent;
  font-size: 1.25rem;
}

.exam-support-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: .5rem;
  margin-top: 1.25rem;
}
</style>
