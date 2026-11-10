# Admin egress controls

- Processing status refreshes every 15 seconds only while the page is visible,
  the Processing section is selected, and queued/active work was reported.
  An idle queue requires manual refresh to discover work started in another browser.
- Upload status refreshes every 5 seconds after an immediate initial status read.
  Hidden pages pause polling. Completed/failed/paused jobs stop it.
- Polls do not overlap. Failures back off to at most one request per 60 seconds;
  successful reads restore the normal interval. Unmount removes listeners/timers.
- Browser-driven batch processing finishes its current PDF, then pauses if hidden.
  Use Resume processing when returning. Server workers are not cancelled.
- Admin campaign summaries read only necessary paper fields and latest ingestion
  paper IDs/statuses; level filtering happens in SQL. The existing bounded cache
  stores only the compact summary, for at most 15 seconds, in an admin scope.
  Ingestion status commits invalidate that scope without evicting student snapshots.
  Processing/retry mutations bypass summary caching when choosing eligible papers.
- No schema changes, extra workers, or larger RAM cache budget are required.

Historical query counters and billed egress are different metrics. Do not claim a
monthly GB or CPU percentage reduction from polling intervals alone. Compare
subsequent dashboard egress under similar traffic and admin usage. Existing egress
is not reversed by this deployment.

## Paper reads and invalidation

Student snapshots and solution-summary version checks select only the five
evidence keys used by the snapshot builder. Debug evidence remains stored in the
database and available to editors. A separate read-only ORM identity map shares
the request connection, so partial evidence cannot overwrite full editor data or
consume an additional database pool slot. Options and images are select-in loaded
to avoid multiplying question text/evidence across option-image combinations.

Normal question/option/image/solution ORM edits evict the affected paper keys.
Old and new paper ownership are included for moves. Unknown ownership and bulk
SQL changes fall back to broader invalidation. Compact admin summaries retain
their separate 15-second TTL and ingestion-status invalidation. Redis cache writes
atomically verify scope and per-key invalidation tokens; local fills are fenced
against changes during a load. Cache memory limits are unchanged.

OPPE remains an external new-tab homepage link only. Workbook OPPE columns are
not imported; no internal runner/routes are provided. Historical database tables
not represented by the application models are not dropped by this release.
