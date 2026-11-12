# Paper corrections and score/calculator fixes

Admin -> Papers -> Edit questions opens an editor for the selected original,
active paper. Edit details remains separate for title/course/term metadata.
Navigate between question tabs or Previous/Next; drafts persist in the dialog.
Save all changes sends only dirty questions in one request. Text, passage,
options, answer JSON, type, marks, negative marks, tolerance, topic and explanation
can be corrected. Hidden questions stay hidden. Existing images are retained;
use the existing single-question editor for image upload/removal and visibility.

GET/PATCH /api/admin/papers/<id>/questions/edit require admin access and existing
CSRF protection. Reader excludes full extraction evidence using the slim isolated
session and batched child reads. Limit: 125 questions and 2 MiB save payload.
Larger papers use the existing single-question editor. No polling/autosave or
new persistent cache was added. Questions under processing cannot be edited.
Aliases are rejected with an instruction to edit the original paper.

Every dirty question's version is checked and all input is validated before the
first mutation. One transaction stores all corrections and per-question audit
history; conflicts/errors retain drafts in the browser and commit nothing.
Existing undo handles each question's latest EDIT. A lost save response may show
409 on retry; reopen to verify the saved values. Existing temporary attempts
retain immutable snapshots. Current paper/solution caches use existing targeted
invalidation; corrected content invalidates outdated published solution versions.

Issue #10: Calculator has its own light theme and scoped explicit colors,
including number/function keys, display, header, memory keys and resize handle.
Dark exam theme, calculations, dragging and resizing remain available.

Issue #11: New submissions calculate marks/percentage using available questions
with known marks and grading data, including skipped gradable questions in the
denominator. Missing/ungradable questions are excluded, never guessed. When
anything is excluded, results/share cards label the available graded score and
the result includes partial_score/excluded_from_score. No eligible positive
marks means no percentage. Partial percentages do not enter the reliably graded
exam analytics or appear as full-paper percentages in local progress. Existing
submitted receipts are not bulk recalculated; retake to see the new calculation.
The source PDF's declared marks do not replace the available-question denominator.

No migrations, R2 copies, increased worker counts or cache budgets. Deploy clears
local RAM caches once; editing rebuilds affected content caches when next used.
No production question/attempt was created or modified to test this change.

Validation: Vue production build passed. Full frontend suite passed 146 tests;
an additional subset-score test passed, plus focused editor/result/calculator
coverage. Backend tests cover batch atomicity, stale version rejection, unchanged
attempt snapshots, hidden-state preservation, admin/CSRF guards, processing
conflicts, slim reader SQL, subset marks and analytics exclusion.

Full SQLite backend suite: 358 passed. No live data was edited for testing.
