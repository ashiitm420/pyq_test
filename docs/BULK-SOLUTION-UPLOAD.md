# Bulk solution uploads

Admin → Solutions supports selecting up to 50 papers, including a button to select the first 50 filtered papers. Export includes question identities, available PDFs (100 MB total) and the detailed solution prompt. Missing PDFs are listed in the ZIP README. No AI runs automatically on export.

Prepare verified solutions in manageable groups and combine their paper objects into one `pyq-solutions-bundle-v1` JSON file (up to 100 MB, at most 50 papers). Existing per-paper limits remain: 200 questions, 2 MB JSON, 8,000 explanation characters and 1,200 characters per option. Preview before saving.

The browser previews and saves one paper per request to avoid one long 50-paper import transaction. A failed paper does not stop other papers. Pause stops after the active paper. Retry failed papers processes only failures; Resume remaining skips successful papers. Keep the page open during processing.

After a reload, select the identical file and replacement setting, preview again, then resume. Only compact result receipts are saved in browser storage, keyed by a SHA-256 fingerprint of the file and replacement setting; solution text is not stored there. Preview revalidates against the current database. If storage is unavailable, the UI explains the limitation.

The API's opt-in `skip_identical` flag compares exact version, explanation, final answer, checks and publication status against persisted solutions. Replaying an already committed request does not change it, even if the browser lost the response. Different existing content still requires explicit replacement. Flagged answers stay unpublished. Database question-version and active-worker checks still apply.

The prompt asks for simplest English, given values, formulas and symbol meanings, justified substitutions, intermediate calculations, units/rounding, conceptual reasoning, and explanations for every choice. There is no fixed step count. Import checks validate structure and answer-key consistency, not the truth or completeness of the reasoning; review the content before publishing.
