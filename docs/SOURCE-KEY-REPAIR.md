# Source-verified answer-key repair, 16 November 2026

Scope: 215 available objective questions marked ungraded, excluding 129 Subjective questions. The verified manifest contains **200 corrections: 199 NAT and one MSQ**. The remaining 15 are listed in `answer-key-repair-remaining.csv` and are not changed. No new Content Reports are created.

## Evidence and recovery

197 unlocked numerical keys are read conservatively from the original stored PDF extraction (`evidence.raw_answer`). The failed extraction included the next subject title and labelled Section Id after a valid key. Eight Industry 4.0 source PDFs were downloaded and checked, including visually inspected source keys; the same exact numeric parser validates all manifest values/ranges. Additional available PDFs were cross-checked against source question IDs, key text and original PDF SHA-256 object names. No R2 object was uploaded or duplicated.

Two additional numerical keys (questions 16118 and 19665) are visually verified on the original PDF: 4, and inclusive range 2.4–2.6. Their PDFs end with the next course heading but no Section Id; these are explicit one-time corrections, not a rule to guess unknown parser tails. MSQ 7879 has source-green options 6406536375935 and 6406536375937, both verified against existing option IDs.

The eight Industry pilot corrections are: 20026 → 16; 21354 → 2700; 22276 → 9.4–9.6 inclusive; 22544 → 4; 24562 → 300; 26918 → 21656–22094 inclusive; 27876 → −36 to −30 inclusive; 28603 → 114. The last example in some split PDFs can belong to another subject; this repair changes only its explicit grading key and does not hide/reclassify questions or implement the deferred boundary-review policy.

Unresolved cases include truncated source keys/options, two scanned questions whose correct option IDs/diagrams were not properly extracted, and one manually locked question. No keys are inferred by eliminating red options or by solving incomplete questions.

## Safe application

Docker runs `flask repair-verified-keys` after normal migrations, before Gunicorn and public cache warmup. The command applies the bundled manifest only once per database, with a small ImportRun receipt. Subsequent startups perform one small receipt lookup returning only its ID (no question/manifest/PDF reload and no learner-request work).

The initial transaction locks affected paper/question rows, skips archived/processing papers, checks the exact question ID, paper/file ID, number, type, source question ID, marks, previous key/status, update timestamp and manual lock. Changes made by an administrator after the audit are skipped rather than overwritten. All accepted corrections and the receipt commit atomically; a failure rolls back. The command does not alter text, passages, marks, options, images or Subjective questions.

Every change has a `SOURCE_KEY_REPAIR` QuestionReview entry using the existing full before/after history. Existing admin Undo works. Keys receive a manual-protection flag, preserving the correction on later imports. Already active/submitted attempt snapshots are unchanged; start a fresh attempt to grade against the repaired key.

Existing ORM after-commit hooks invalidate the affected paper snapshots and solution maps plus catalog summaries. No new global cache policy, polling, schema, worker, cache budget or scheduled job is introduced. The one-time manifest is about 129 KB; PDFs/extraction run locally, not on Render. The existing negative-marking policy remains zero.

## Future parser behavior

`parse_numeric_answer_block` accepts explicit numeric key lines and stops only at a labelled numeric Section Id, optionally preceded by one section-title line. Unrecognized or malformed tails remain ungraded rather than being guessed. It does not hold papers or create review reports. Metadata is not included in the answer key.

## Verification

Tests cover source boundaries, ranges/alternatives, ambiguous text rejection, all eight Industry pilot grades, idempotence, concurrent edits/manual locks/processing guards, rollback, history/Undo, unchanged old attempt snapshots and refreshed cached paper grading. Verify actual post-deploy applied/skipped totals from the ImportRun receipt and re-run the ungraded aggregate; target after 200 unchanged candidates is 144 total (129 Subjective + 15 unresolved objective).
