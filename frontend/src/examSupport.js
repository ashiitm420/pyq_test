// A successful submission can show the card once, on its immediate result view.
let pendingAttemptId = null;

export function offerExamSupport(attempt) {
  pendingAttemptId = attempt?.status === 'SUBMITTED' && attempt.mode === 'exam'
    ? attempt.id
    : null;
}

export function consumeExamSupport(attemptId) {
  if (pendingAttemptId === null || pendingAttemptId !== attemptId) return false;
  pendingAttemptId = null;
  return true;
}
