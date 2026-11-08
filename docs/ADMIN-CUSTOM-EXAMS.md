# Admin custom exams (experimental)

Admin → Custom exam. Select 1–4 available papers across courses, quizzes and terms, set 1–480 minutes, confirm and start. All selected papers share one deadline. Tabs switch locally and retain answers and the last visited question. Any question can be opened from the selected paper's palette. Submit confirms per-paper answered/review counts and submits all papers. Results include the combined score, source-paper scores and question review; custom review defaults to one question at a time to avoid rendering all maths/images together. Existing calculator, scratchboard, save journal and server expiry apply.

This is restricted on the server to the creating administrator AND originating visitor session. Logout blocks reads, saves and submission until that administrator signs in again. The feature is not on public home/course pages. Custom exam mode switching is intentionally unavailable. Starting replaces that browser's unfinished attempt after all selection/content checks succeed. Scores/review expire one hour after submission; custom scores are not saved to the browser's single-paper progress and generate no normal analytics events. No tables or migration were added: the small existing attempt context JSON stores section metadata.

## Resource limits and tradeoffs

- Maximum 4 distinct source papers, 100 total available questions and 1 MiB serialized private snapshot content. Reject oversized/empty/archived selections; never silently truncate a paper. Aliases of one source cannot be combined.
- Reuse immutable, bounded shared paper snapshot caches. Count questions in one grouped query before loading source content. Reuse one batched answer insert and existing batched autosaves. One extra non-queuing worker-local custom-start slot supplements the existing start gate.
- Bounded question text is bootstrapped once, allowing navigation without question requests. This deliberately trades a bounded initial payload for fewer requests and transactions during the exam. No photo bytes are embedded in snapshots. Custom image prefetch is disabled; images load when their question is rendered. Signed R2 delivery remains available when every selected source has verified image assets; otherwise the existing reliable proxy fallback applies.
- No runtime AI, scheduler, new worker, new cache, or per-paper heartbeat. The existing 10–15 minute timer safety heartbeat remains; normal solving reuses existing save requests. Status does not load answer rows.
- Grade once using original snapshots and marking rules, then group the already-graded rows for paper summaries. Duplicate submits return the existing result. Expired submissions cannot introduce late answers. Unknown keys/marks follow the existing ungraded/provisional rules.
- SQL operations and bounded Python work still consume resources. Cold-cache starts, images and concurrent users can be slower; no production throughput or OOM guarantee is implied.

## Validation

`pytest tests/test_custom_exam.py tests/test_custom_exam_budget.py -q -s`

`cd frontend && npx vitest run tests/custom-exam.spec.js && npm run build`

The local budget fixture compares one 80-question paper against four 20-question papers, with warm source caches, SQLite, no images and isolated test data. In one run both used 9 SQL statements for start and 4 for one answer save; response sizes were 36.6 and 37.1 KiB. Python traced allocation peaks were 829 and 577 KiB respectively. These are allocation traces, not process RSS or the Render instance's RAM; timings are not representative of production latency. The test asserts bounded query growth, not timing or memory ratios.

Manual admin check: select two different courses, set a short duration, answer and mark questions in both sections, switch back, refresh, submit, inspect per-paper scores; then sign out and verify the same attempt URL is denied. A guest's POST with `paper_ids` must return 403. Never use production traffic for capacity tests.
