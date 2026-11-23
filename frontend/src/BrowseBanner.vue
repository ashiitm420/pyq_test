<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

// Keep the parser-inserted tag and its creative in their original document.
const banner = document.getElementById('mauryahub-browse-banner');
const slot = ref(null);
const filled = ref(false);
let size, creative, frame;

function alignBanner() {
  const bounds = slot.value?.getBoundingClientRect();
  if (!banner || !bounds) return;
  banner.hidden = !filled.value || bounds.width < 320;
  if (banner.hidden) return;
  banner.style.left = `${bounds.left + window.scrollX + bounds.width / 2}px`;
  banner.style.top = `${bounds.top + window.scrollY}px`;
}

function scheduleAlignment() {
  cancelAnimationFrame(frame);
  frame = requestAnimationFrame(alignBanner);
}

function updateCreative() {
  filled.value = Boolean(banner.querySelector('iframe'));
  scheduleAlignment();
}

onMounted(() => {
  if (!banner || !slot.value) return;
  creative = new MutationObserver(updateCreative);
  creative.observe(banner, { childList: true, subtree: true });
  if (typeof ResizeObserver !== 'undefined') {
    size = new ResizeObserver(scheduleAlignment);
    size.observe(slot.value);
    size.observe(document.body);
  }
  window.addEventListener('resize', scheduleAlignment);
  updateCreative();
});

onUnmounted(() => {
  if (!banner) return;
  creative?.disconnect();
  size?.disconnect();
  cancelAnimationFrame(frame);
  window.removeEventListener('resize', scheduleAlignment);
  banner.hidden = true;
});
</script>

<template>
  <div v-if="banner" class="browse-ad-region" aria-hidden="true">
    <div ref="slot" class="browse-ad-spacer" :class="{ 'has-creative': filled }"></div>
  </div>
</template>

<style>
.browse-ad-region { container-type: inline-size; }
.browse-ad-spacer.has-creative { min-height: 68px; margin: 20px 0; }
@container (width < 320px) {
  .browse-ad-spacer.has-creative { min-height: 0; margin: 0; }
}
#mauryahub-browse-banner:not([hidden]) {
  position: absolute;
  transform: translateX(-50%);
  display: flex;
  width: 320px;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--muted, #63758d);
}
#mauryahub-browse-banner small { font-size: 10px; line-height: 14px; }
#mauryahub-browse-banner iframe { display: block; border: 0; }
</style>
