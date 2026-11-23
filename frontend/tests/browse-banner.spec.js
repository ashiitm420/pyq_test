import { afterEach, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import BrowseBanner from '../src/BrowseBanner.vue';
import { needsBannerDocument } from '../src/navigation';

afterEach(() => {
  document.getElementById('mauryahub-browse-banner')?.remove();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it('renders nothing without a server-supplied tag', () => {
  const wrapper = mount(BrowseBanner);
  expect(wrapper.find('.browse-ad-spacer').exists()).toBe(false);
  wrapper.unmount();
});

it('positions the vendor frame without moving or recreating it', async () => {
  const banner = document.createElement('aside');
  banner.id = 'mauryahub-browse-banner';
  banner.hidden = true;
  document.body.append(banner);
  let align;
  vi.stubGlobal('requestAnimationFrame', callback => { align = callback; return 1; });
  const wrapper = mount(BrowseBanner);
  const slot = wrapper.get('.browse-ad-spacer');
  vi.spyOn(slot.element, 'getBoundingClientRect').mockReturnValue({ left: 20, top: 80, width: 400 });
  align();
  expect(banner.hidden).toBe(true);
  expect(slot.classes()).not.toContain('has-creative');

  const creative = document.createElement('iframe');
  banner.append(creative);
  await Promise.resolve();
  await wrapper.vm.$nextTick();
  align();
  expect(slot.classes()).toContain('has-creative');
  expect(banner.hidden).toBe(false);
  expect(banner.style.left).toBe('220px');
  expect(banner.style.top).toBe('80px');
  expect(creative.parentNode).toBe(banner);

  wrapper.unmount();
  expect(banner.hidden).toBe(true);
  expect(creative.parentNode).toBe(banner);
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
