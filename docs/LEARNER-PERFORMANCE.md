# Learner flow changes

This change targets unnecessary work on the existing single Render Free instance.
It does not add workers, services, polling or a larger memory budget.

- Import status/retry/event ORM updates preserve public caches. A changed file
  path or paper still refreshes download availability. Bulk ingestion writes
  conservatively refresh catalog data, but preserve question snapshots.
- Source-entry bookkeeping no longer invalidates public content; changes to
  actual papers and questions still invalidate all relevant content.
- AI solution writes refresh coverage/solution counts and published solutions,
  while keeping reusable question snapshots. Local and Redis caches use the
  same invalidation scopes. Existing byte, entry and TTL limits remain.
- Public course reads now participate in the existing browser request cache,
  including the course detail records already primed by the homepage.
- Course topics load after the primary paper list and cannot fail the page.
- Remove unconditional Exam and Records module warmups on the homepage and
  automatic question warmup on paper-detail entry. Prepare the Exam module on
  Start-button pointer/focus intent only, after a brief idle delay. Skip optional
  prefetch on hidden pages, data saver and 2G/3G connections; cancel on unmount.
- Calculator opens at a compact 540 by 490 CSS pixels, constrained to the
  viewport. Its body scrolls when necessary. Manual resize remains
  available, and viewport changes clamp its size/position to the screen.

No production latency percentage is claimed. Compare repeated catalog/course/
attempt starts with the same workload after rollout, including while imports
run. Question navigation, answer batching, grading and timer rules are unchanged.
