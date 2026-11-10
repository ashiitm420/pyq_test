# Reuse paper content across public read paths

This completes an additional egress-reduction pass on top of slim evidence,
compact admin summaries, visibility-aware polling, and paper-specific cache
invalidation. It is not a claim of a measured 60–70% organization-wide saving.

## Changes

- Public `/study/papers/<id>` reuses quiz snapshots and published-solution maps.
  With these caches warm, the page reads no question/option/image/solution content
  from PostgreSQL. Paper metadata is still checked each request so archived
  papers return 404. HTML, advertising consent and student state are not cached.
- Public `/study/images/<id>` selects only the asset path and active-image IDs,
  checking current question and paper visibility. It no longer reads the full
  parent question, extraction evidence, all options and all sibling images.
  Active-image removal and paper archival continue returning 404 immediately.
- Custom-exam review and practice feedback reuse each contributing paper's
  solution map; single-question solution reads also reuse that map. Current
  content version and stored-attempt version must both match. Unpublishing or
  editing invalidates the same existing cache keys.
- Published-solution cache loads only ID/version/text, not provider diagnostics,
  final-answer JSON and review metadata.
- Admin question lists fetch options/images in two batches per page instead of
  two lazy queries per question. Full editor evidence remains available.
- Search projects four preview columns and truncates question text in SQL.
- Diploma inventory/reset reads question IDs rather than complete question rows.
  No reset is executed by this update.
- Analytics question-attention reads options/images separately to avoid the
  option × image join multiplying the parent question/evidence payload.

## Limits preserved

No R2 objects, replicas, migrations, paid services, new background polling,
workers or larger cache allocation. The existing bounded cache budget, TTLs,
miss coalescing, Redis fencing and invalidation remain unchanged. An evicted or
cold paper still reads PostgreSQL once when needed. Opt-in advertising retains
its current complete editorial checks, so that path can still read questions.
Local benchmarks do not prove production peak RSS, CPU or latency.

## Evidence and measurement

Regression tests assert warm SSR content reads = 0, image permission lookup =
one lightweight SELECT with no option/body query, custom review warm reads = 0,
admin child reads = two batches, and search excludes evidence/answer keys.
These are path-specific query improvements, not billed-byte percentages.

Read-only predeployment snapshot, 2026-11-10 15:27:05 UTC:

| Query ID | Calls | Rows |
| --- | ---: | ---: |
| -2490488656883095293 | 12335 | 250395 |
| -63495015688199076 | 1741 | 2036645 |
| 1474690727393381948 | 200460 | 1153602 |
| 2105483575096345288 | 177091 | 546816 |
| 2795969432108486036 | 78 | 1474 |
| 5042882937727078274 | 1883 | 807160 |

Stats are cumulative; do not reset them. Compare deltas over similar traffic
and Supabase's daily egress chart after deployment. Existing cycle usage never
falls when optimizations deploy: only subsequent growth slows. An unchanged
legacy query still growing could come from another script or old local server;
application names currently do not conclusively identify its caller.

```sql
SELECT now() AS checked_at, queryid, calls, rows
FROM pg_stat_statements
WHERE queryid IN (-2490488656883095293, -63495015688199076,
  1474690727393381948, 2105483575096345288,
  2795969432108486036, 5042882937727078274)
ORDER BY queryid;
```

A 60–70% overall target depends on how much traffic hits these paths and other
clients. It cannot be guaranteed from query counts or a short smoke test. If the
site remains over quota, assess measured traffic before introducing durable
cache replicas, since these add storage, cache-coherency and operation costs.

## Validation

Full SQLite backend suite: 350 passed. The new read-path suite: 5 passed
(includes two tests added after the full run began). Python compile and
`git diff --check` passed. No production records were created for testing.
