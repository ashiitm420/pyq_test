# Free-tier learner capacity changes

This release adds no service, worker, persistent queue or larger cache budget.

## Implemented

- Hashed build assets use an empty session and skip session-cookie saving and
  application rate-limit bookkeeping. They retain immutable cache headers and
  no longer vary by Cookie. Login/session/API behavior remains separate.
- PurgeCSS trims only Bootstrap during production builds. App and KaTeX rules
  are untouched; dynamic Bootstrap controls/states have a safelist. Homepage CSS
  measured 291.4 KiB raw / 44.2 KiB gzip before and 131.7 KiB raw / 25.1 KiB gzip
  after. These are local build sizes, not a latency measurement.
- KaTeX CSS is imported by math components instead of the SPA entry, so it is
  absent from the homepage's initial CSS. Public study pages keep their math CSS.
- `EXAM_START_CONCURRENCY` defaults to 2 per worker. Extra simultaneous starts
  get HTTP 503, code `START_BUSY`, and Retry-After: 3 before loading questions or
  creating attempts. No waiting queue or automatic POST retry is added. This
  protects starts, not all traffic or every possible OOM allocation.
- Admin Overview has an Exam priority switch that pauses new heavy import/PDF
  requests. Running work finishes normally. This switch is worker-local and
  resets on restart; it fits the existing single-worker service, not a future
  multi-worker deployment. It does not pause analytics or the deferred AI summary.
- Leaving an exam page no longer deletes its active attempt. Pending-answer
  journals survive within the same tab, and a browser-stored Resume pointer is
  shown on other learner pages. Server ownership, expiry and deadlines remain
  authoritative. Timers continue while away; a new test still replaces the old
  active test. Pending unsent answers do not transfer to another tab/device.
  Submission expires an overdue attempt before merging client drafts, so a
  resumed browser cannot introduce unsent answers after the server deadline.
- Existing answer writes were already batched into a bounded read/commit; no
  extra autosave traffic, polling or browser-side exam answer keys are added.

## Verification tools

`python scripts/audit_paper_images.py PAPER_ID` performs up to 500 sequential R2
metadata checks outside HTTP requests. It only reports missing/empty objects;
it neither publishes assets nor changes verified flags. Production object
coverage and image integrity still need an authorized maintenance audit.

`python scripts/capacity_smoke.py --base-url http://127.0.0.1:5089 --paper-id 1
--users 2 --confirm-isolated-staging` exercises independent cookie sessions,
home/catalog reads, exam start, answer-write marking and submit. It forbids known
production hostnames and caps concurrency at 20. Use disposable staging data;
the script creates and submits attempts. Increase gradually and observe errors,
latency, CPU and RSS. A local SQLite smoke test is not Render/Postgres capacity.

## External work and limits

Removing cookie-dependent asset behavior makes responses suitable for shared
static caching; it does not enable a Cloudflare zone or guarantee edge hits.
Cloudflare account/DNS/cache-rule changes are not part of this code release.
Keep private admin/session/answer/attempt APIs out of shared caches. Signed R2
delivery already exists for verified papers; unverified assets keep their safe
fallback. No bulk asset rewrite or production load test has been performed.

Free-tier sleeping, finite CPU/RAM and upstream database limits still apply.
Do not claim a concurrent-user capacity or fixed latency saving from build sizes
or the start semaphore alone. Existing Server-Timing/slow-request/RSS sampling
is retained for post-deploy measurements.
