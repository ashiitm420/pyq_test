<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

const key = '04b45b8b141ae47be2afd0bd9dac1a47';
const containerId = 'atContainer-' + key;
const enabled = document.querySelector('meta[name="mauryahub-browse-ads"]')?.content === 'active';
const slot = ref(null);
let resize, visibility, visible = false;

function loadWhenReady() {
  if (!visible || !slot.value || slot.value.clientWidth < 320) return;
  if (document.querySelector('script[data-mauryahub-banner]')) return;
  resize?.disconnect();
  visibility?.disconnect();
  if (!Array.isArray(window.atAsyncOptions)) window.atAsyncOptions = [];
  window.atAsyncOptions.push({
    key, format: 'js', async: true, container: containerId, params: {},
  });
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://bauval.org/22/' + key;
  script.dataset.mauryahubBanner = '';
  document.head.append(script);
}

onMounted(() => {
  if (!slot.value) return;
  if (typeof ResizeObserver !== 'undefined') {
    resize = new ResizeObserver(loadWhenReady);
    resize.observe(slot.value);
  }
  if (typeof IntersectionObserver !== 'undefined') {
    visibility = new IntersectionObserver(entries => {
      visible = entries.some(entry => entry.isIntersecting);
      loadWhenReady();
    }, { rootMargin: '100px' });
    visibility.observe(slot.value);
  } else {
    visible = true;
    loadWhenReady();
  }
});

onUnmounted(() => {
  resize?.disconnect();
  visibility?.disconnect();
});
</script>

<template>
  <div v-if="enabled" class="browse-ad-region">
    <aside ref="slot" class="browse-ad" aria-label="Advertisement">
      <small>Advertisement</small>
      <div :id="containerId" class="browse-ad-creative"></div>
    </aside>
  </div>
</template>

<style scoped>
.browse-ad-region { container-type: inline-size; }
.browse-ad {
  display: grid;
  justify-items: center;
  gap: 4px;
  margin: 20px 0;
  color: var(--muted, #63758d);
}
.browse-ad small { font-size: 10px; line-height: 14px; }
.browse-ad-creative { width: 320px; min-height: 50px; }
@container (width < 320px) {
  .browse-ad { display: none; }
}
</style>
