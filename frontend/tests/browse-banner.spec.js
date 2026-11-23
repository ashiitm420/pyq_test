import { afterEach, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import BrowseBanner from '../src/BrowseBanner.vue';
import { needsBannerDocument } from '../src/navigation';

afterEach(() => {
  document.head.querySelectorAll('meta[name="mauryahub-browse-ads"], script[data-mauryahub-banner]').forEach(node => node.remove());
  delete window.atAsyncOptions;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it('renders nothing with ads disabled', () => {
  const wrapper = mount(BrowseBanner);
  expect(wrapper.find('aside').exists()).toBe(false);
  expect(document.querySelector('script[data-mauryahub-banner]')).toBeNull();
  wrapper.unmount();
});

it('loads one async script when the visible slot fits, using the provider container', () => {
  let notify;
  vi.stubGlobal('IntersectionObserver', class {
    constructor(callback) { notify = callback; }
    observe() {}
    disconnect() {}
  });
  const marker = document.createElement('meta');
  marker.name = 'mauryahub-browse-ads';
  marker.content = 'active';
  document.head.append(marker);
  const wrapper = mount(BrowseBanner);
  const spot = wrapper.get('aside');
  Object.defineProperty(spot.element, 'clientWidth', { value: 300, configurable: true });
  notify([{ isIntersecting: true }]);
  expect(document.querySelector('script[data-mauryahub-banner]')).toBeNull();
  Object.defineProperty(spot.element, 'clientWidth', { value: 320 });
  notify([{ isIntersecting: false }]);
  expect(document.querySelector('script[data-mauryahub-banner]')).toBeNull();
  notify([{ isIntersecting: true }]);
  notify([{ isIntersecting: true }]);

  const scripts = document.querySelectorAll('script[data-mauryahub-banner]');
  expect(scripts).toHaveLength(1);
  expect(scripts[0].async).toBe(true);
  expect(scripts[0].src).toMatch(/^https:\/\/bauval\.org\/22\//);
  const container = spot.get('.browse-ad-creative').attributes('id');
  expect(window.atAsyncOptions).toEqual([expect.objectContaining({ format: 'js', container })]);
  expect(wrapper.find('iframe').exists()).toBe(false);
  wrapper.unmount();
});

it('refreshes browse documents and keeps exam start and submit navigation in-app', () => {
  expect(needsBannerDocument('/', '/exam/Quiz%201', 'active')).toBe(true);
  expect(needsBannerDocument('/exam/Quiz%201', '/paper/1', 'active')).toBe(true);
  expect(needsBannerDocument('/result/1', '/', 'available')).toBe(true);
  expect(needsBannerDocument('/paper/1', '/attempt/1', 'active')).toBe(false);
  expect(needsBannerDocument('/attempt/1', '/result/1', 'active')).toBe(false);
  expect(needsBannerDocument('/paper/1', '/admin', 'active')).toBe(true);
  expect(needsBannerDocument('/', '/paper/1', '')).toBe(false);
});
