# Add missing questions

Admin → Papers → choose the existing paper → **Add / append questions**.
Also available in Question bank after selecting a paper.

1. Enter the original missing question number, text/formulas, options, answer key
   (or `null` when unknown), marks and optional passage/explanation.
2. Use **+ Add another** to assemble up to 20 questions, maximum 256 KB per batch.
3. By default additions are hidden drafts. Choose immediate publication only if
   all questions are complete; otherwise save, open **Edit / add image**, upload
   PNG/JPEG images using the existing editor, then **Restore question** to publish.
4. Existing question numbers cannot be reused. Edit/restore those questions instead.
   Question numbers determine the existing natural order; old rows are not renumbered.

The batch is validated and committed atomically. A retained browser request ID
prevents duplicate creation when retrying after an uncertain response. Archived,
alias and currently-processing papers reject new additions. Use the canonical
source paper for aliases. New rows are admin-locked against automatic replacement,
with audit history; hide an added question to withdraw it from new attempts.
Existing attempt snapshots/results do not acquire the new questions retroactively.

This is a manual text/formula batch form, not PDF extraction or a replacement-PDF
append mode. Images are attached after saving drafts. No new schema, timer,
background worker, AI call, or automatic student-side request is added.
