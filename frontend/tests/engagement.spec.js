import { it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import Records from '../src/Records.vue';
import QuizRecap from '../src/QuizRecap.vue';
import { offerExamSupport } from '../src/examSupport';
import { api } from '../src/api';

vi.mock('../src/api', () => ({ api: vi.fn(), go: vi.fn(), session: {} }));

const attempt = {
  id: 5, status: 'SUBMITTED', mode: 'exam', title: 'Quiz 1',
  expires_at: 2000000000, palette: [], result: { score: 5, total_marks: 10, percentage: 50 },
};
const mountResult = (id = attempt.id) => mount(Records, {
  props: { route: '/result/' + id },
  global: { stubs: { ShareResult: true } },
});

beforeEach(() => {
  offerExamSupport(null);
  vi.resetAllMocks();
  api.mockResolvedValue(attempt);
});

it('offers support once immediately after each exam submission and keeps review available', async () => {
  offerExamSupport(attempt);
  const first = mountResult();
  await flushPromises();
  expect(first.get('.exam-support').text()).toContain('Help keep MauryaHub running');
  expect(first.get('.result-question-summary').text()).toContain('Question review');
  expect(first.find('[role="dialog"]').exists()).toBe(false);
  expect(api.mock.calls).toEqual([['/attempts/5']]);
  await first.get('.exam-support .btn-light').trigger('click');
  expect(first.find('.exam-support').exists()).toBe(false);
  first.unmount();

  const revisit = mountResult();
  await flushPromises();
  expect(revisit.find('.exam-support').exists()).toBe(false);
  revisit.unmount();

  const next = { ...attempt, id: 6 };
  offerExamSupport(next);
  api.mockResolvedValue(next);
  const second = mountResult(6);
  await flushPromises();
  expect(second.find('.exam-support').exists()).toBe(true);
  await second.get('.exam-support .btn-outline-primary').trigger('click');
  await vi.waitFor(() => expect(second.get('[role="dialog"]').text()).toContain('Continue to payment'));
  expect(api.mock.calls).toEqual([['/attempts/5'], ['/attempts/5'], ['/attempts/6']]);
  second.unmount();
});

it('skips the support card on practice results and direct result visits', async () => {
  const practice = { ...attempt, mode: 'practice' };
  offerExamSupport(practice);
  api.mockResolvedValue(practice);
  const result = mountResult();
  await flushPromises();
  expect(result.find('.exam-support').exists()).toBe(false);
  result.unmount();

  api.mockResolvedValue(attempt);
  const directVisit = mountResult();
  await flushPromises();
  expect(directVisit.find('.exam-support').exists()).toBe(false);
  directVisit.unmount();
});

it('renders real snapshot numbers and no live request', () => {
  const w = mount(QuizRecap);
  expect(w.text()).toContain('2,300');
  expect(w.text()).toContain('500');
  expect(w.text()).toContain('200');
  expect(w.text()).toContain('Reach estimated from participating browsers');
  expect(w.text()).not.toContain('QUIZ 1');
  expect(api).not.toHaveBeenCalled();
  w.unmount();
});
