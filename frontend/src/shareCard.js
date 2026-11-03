// Result share card: drawn entirely in the student's browser (canvas).
// No server request, no upload: nothing is added to Render CPU or storage.
// The card never contains a name, attempt ID or answers, only the paper and score.
import {displayExamTitle} from './displayTitle';

export const CARD_WIDTH = 1080, CARD_HEIGHT = 1350;
const FONT = 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

function clockText(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0)), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  if (h) return `${h}h ${m}m`;
  return m ? `${m}m ${s % 60}s` : `${s}s`;
}

const number = value => (value === null || value === undefined || Number.isNaN(Number(value))) ? null : Number(value);
const trim = value => String(Math.round(value * 100) / 100);

export function shareSummary(attempt, origin = (typeof window !== 'undefined' ? window.location.origin : '')) {
  const r = attempt?.result;
  if (!r) return null;
  const percentage = number(r.percentage), score = number(r.score), total = number(r.total_marks);
  const questions = attempt.palette?.length || 0;
  const link = (origin || '') + (attempt.paper_id ? '/paper/' + attempt.paper_id : '/');
  return {
    title: displayExamTitle(attempt.title || ''),
    percentage,
    score: score === null ? null : trim(score),
    total: total === null ? null : trim(total),
    provisional: Boolean(r.pending_manual),
    correct: r.correct ?? 0,
    incorrect: r.incorrect ?? 0,
    partial: r.partial ?? 0,
    attempted: r.attempted ?? 0,
    questions,
    accuracy: number(r.accuracy),
    time: clockText(r.time_taken),
    link,
    host: (origin || '').replace(/^https?:\/\//, '').replace(/^www\./, '') || 'mauryahub.in',
  };
}

export function headline(s) {
  if (s.percentage !== null) return `${Math.round(s.percentage)}%`;
  if (s.score !== null && s.total !== null) return `${s.score}/${s.total}`;
  return `${s.correct}/${s.questions}`;
}

export function shareText(s) {
  const marks = s.score !== null && s.total !== null ? ` (${s.score}/${s.total} marks)` : '';
  const what = s.percentage !== null ? `${trim(s.percentage)}%${marks}` : (marks ? marks.slice(2, -1) : `${s.correct} correct out of ${s.questions}`);
  return `I scored ${what}${s.provisional ? ' (provisional)' : ''} in ${s.title} on MauryaHub.\nPractise IITM BS previous-year papers free: ${s.link}`;
}

// Greedy word wrap with an injectable measure, so it is unit-testable without canvas.
export function wrapLines(text, maxWidth, measure, maxLines = 3) {
  const words = String(text).split(/\s+/).filter(Boolean), lines = [];
  let line = '';
  for (const word of words) {
    const next = line ? line + ' ' + word : word;
    if (measure(next) <= maxWidth || !line) line = next;
    else { lines.push(line); line = word; }
  }
  if (line) lines.push(line);
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    let last = kept[maxLines - 1];
    while (last && measure(last + '…') > maxWidth) last = last.slice(0, -1);
    kept[maxLines - 1] = last.trimEnd() + '…';
    return kept;
  }
  return lines;
}

function fitText(ctx, text, x, y, weight, size, maxWidth) {
  let px = size;
  ctx.font = `${weight} ${px}px ${FONT}`;
  while (px > 14 && ctx.measureText(text).width > maxWidth) { px -= 2; ctx.font = `${weight} ${px}px ${FONT}`; }
  ctx.fillText(text, x, y);
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

export function drawShareCard(canvas, s) {
  canvas.width = CARD_WIDTH; canvas.height = CARD_HEIGHT;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Your browser could not create the share image.');
  const W = CARD_WIDTH, pad = 80;
  // Background and header band.
  ctx.fillStyle = '#f5f7fb'; ctx.fillRect(0, 0, W, CARD_HEIGHT);
  const band = ctx.createLinearGradient(0, 0, W, 360);
  band.addColorStop(0, '#172e54'); band.addColorStop(1, '#285fd8');
  ctx.fillStyle = band; ctx.fillRect(0, 0, W, 360);
  ctx.textBaseline = 'alphabetic'; ctx.fillStyle = '#ffffff';
  ctx.font = `800 58px ${FONT}`; ctx.fillText('Maurya', pad, 130);
  const mw = ctx.measureText('Maurya').width;
  ctx.font = `400 58px ${FONT}`; ctx.fillText('Hub', pad + mw, 130);
  ctx.font = `600 24px ${FONT}`; ctx.fillStyle = '#b9d2f2'; ctx.fillText('IITM BS  ·  PREVIOUS-YEAR PAPER PRACTICE', pad, 178);
  // Paper title.
  ctx.fillStyle = '#ffffff'; ctx.font = `650 38px ${FONT}`;
  const titleLines = wrapLines(s.title, W - pad * 2, t => ctx.measureText(t).width, 3);
  titleLines.forEach((line, n) => ctx.fillText(line, pad, 245 + n * 48));

  // Score card.
  const cardY = 400, cardH = 520;
  ctx.fillStyle = '#ffffff'; roundRect(ctx, pad - 20, cardY, W - (pad - 20) * 2, cardH, 32); ctx.fill();
  ctx.strokeStyle = '#e2e8f1'; ctx.lineWidth = 2; ctx.stroke();
  const cx = W / 2, cy = cardY + 225, radius = 170;
  const fraction = s.percentage !== null ? Math.max(0, Math.min(1, s.percentage / 100))
    : (s.score !== null && Number(s.total) > 0 ? Math.max(0, Math.min(1, Number(s.score) / Number(s.total))) : (s.questions ? s.correct / s.questions : 0));
  ctx.lineCap = 'round'; ctx.lineWidth = 30;
  ctx.strokeStyle = '#e7edf7'; ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke();
  if (fraction > 0) {
    ctx.strokeStyle = fraction >= 0.6 ? '#2f8656' : fraction >= 0.35 ? '#285fd8' : '#c9822b';
    ctx.beginPath(); ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * fraction); ctx.stroke();
  }
  ctx.textAlign = 'center'; ctx.fillStyle = '#172e54';
  // Text inside the ring is shrunk until it fits, so long values never overlap it.
  const inner = (radius - 30) * 2;
  fitText(ctx, headline(s), cx, cy + 30, 800, 104, inner - 30);
  ctx.fillStyle = '#708098';
  fitText(ctx, s.provisional ? 'PROVISIONAL SCORE' : 'SCORE', cx, cy + 80, 600, 26, inner - 70);
  ctx.font = `650 34px ${FONT}`; ctx.fillStyle = '#285cbd';
  const marks = s.score !== null && s.total !== null ? `${s.score} / ${s.total} marks` : `${s.correct} of ${s.questions} correct`;
  ctx.fillText(marks, cx, cardY + cardH - 50);

  // Stat tiles.
  const stats = [
    ['Correct', String(s.correct), '#2f8656', '#eaf6ef'],
    ['Incorrect', String(s.incorrect), '#b54646', '#fff0f0'],
    ['Attempted', `${s.attempted}/${s.questions}`, '#285fd8', '#edf3ff'],
    ['Accuracy', s.accuracy !== null ? `${trim(s.accuracy)}%` : '—', '#7b64b0', '#f1edfc'],
  ];
  const gap = 24, tileW = (W - (pad - 20) * 2 - gap * 3) / 4, tileY = 960, tileH = 170;
  stats.forEach(([label, value, fg, bg], n) => {
    const x = pad - 20 + n * (tileW + gap);
    ctx.fillStyle = bg; roundRect(ctx, x, tileY, tileW, tileH, 24); ctx.fill();
    ctx.fillStyle = fg; ctx.font = `800 ${value.length > 5 ? 44 : 54}px ${FONT}`; ctx.fillText(value, x + tileW / 2, tileY + 92);
    ctx.fillStyle = '#5a6d87'; ctx.font = `600 24px ${FONT}`; ctx.fillText(label, x + tileW / 2, tileY + 136);
  });
  ctx.fillStyle = '#5a6d87'; ctx.font = `500 28px ${FONT}`;
  ctx.fillText(`Time taken: ${s.time}${s.partial ? `  ·  Partial: ${s.partial}` : ''}`, cx, 1190);

  // Footer call to action.
  ctx.fillStyle = '#172e54'; ctx.fillRect(0, CARD_HEIGHT - 110, W, 110);
  ctx.fillStyle = '#ffffff'; ctx.font = `650 32px ${FONT}`;
  ctx.fillText(`Practise free at ${s.host}`, cx, CARD_HEIGHT - 45);
  ctx.textAlign = 'left';
  return canvas;
}

export function canvasBlob(canvas) {
  return new Promise((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Could not create the image.')), 'image/png'));
}

export async function buildShareImage(summary, doc = document) {
  try { if (doc.fonts?.ready) await doc.fonts.ready; } catch { /* system font fallback */ }
  const canvas = drawShareCard(doc.createElement('canvas'), summary);
  return canvasBlob(canvas);
}

export function whatsappUrl(text) {
  return 'https://wa.me/?text=' + encodeURIComponent(text);
}
