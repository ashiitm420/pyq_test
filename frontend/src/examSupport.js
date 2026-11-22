// A successful submission can show the card once, on its immediate result view.
let pendingAttemptId = null;
const supportedKey = 'mauryahub:support-confirmed';
let supportedInTab = false;

export function rememberExamSupportPayment() {
  supportedInTab = true;
  try {
    localStorage.setItem(supportedKey, '1');
  } catch {
    // Keep the preference for this tab when browser storage is unavailable.
  }
}

export function hasSupportedMauryaHub() {
  if (supportedInTab) return true;
  try {
    return localStorage.getItem(supportedKey) === '1';
  } catch {
    return false;
  }
}

export function offerExamSupport(attempt) {
  pendingAttemptId = attempt?.status === 'SUBMITTED' && attempt.mode === 'exam'
    ? attempt.id
    : null;
}

export function consumeExamSupport(attemptId) {
  if (pendingAttemptId === null || pendingAttemptId !== attemptId) return false;
  pendingAttemptId = null;
  return !hasSupportedMauryaHub();
}
