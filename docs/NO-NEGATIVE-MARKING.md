# No-negative-marking policy and ungraded feedback

Owner confirmed that all papers have zero negative marking. Grading now applies
that rule centrally: known correct answers earn the configured positive marks;
incorrect answers earn zero even when an imported/active snapshot contains NULL
or a legacy positive penalty. Existing proportional MSQ partial credit remains.
Missing answer keys, correct marks or unsupported subjective grading still need
review and are not fabricated. Skipped gradable questions remain in the marks
denominator even when imported penalty metadata is missing.

Public question responses show negative_marks=0. Both admin correction editors
show a fixed zero penalty; saves normalize it to zero. Original extraction
metadata and stored snapshot content are not mass rewritten, avoiding unnecessary
Supabase transfers and blanket solution-version invalidation. The grading rule
is authoritative regardless of those legacy values. Existing submitted receipts
are not regraded automatically; retake for a newly calculated result.

Investigation (read-only, 12 November 2026): Industry 4.0 Jan 2023 Quiz 1, paper
2154, has 11 AVAILABLE questions with known marks, all missing negative marks;
10 have answer keys. Across available catalog content, 4,403 automatically typed
questions in 238 papers have marks and keys but missing imported penalties.
No answer keys/marks were invented and no production records were edited.

Regression coverage checks MCQ/TRUE_FALSE/NAT/SHORT_TEXT correct feedback,
zero deduction for missing and legacy positive penalties, MSQ partial credit,
missing positive marks, denominator handling and the normal attempt lifecycle.

Validation: full SQLite suite 364 passed; 17 focused append/grading tests passed
on the final append normalization; 20 focused frontend tests plus 3 append tests
and production build passed. No production writes, migration or mass re-extract.
