# Issue #12: points 1–5

The homepage recap replaces the unused homepage course pager below catalog totals, in the requested area. Course pagination remains unchanged. Highlighted Notes buttons open https://mauryahub.onrender.com in a new tab with noopener/noreferrer; OPPE remains just its existing external link.

## Snapshot

`frontend/src/quizRecap.js` holds the 16 Nov database-derived snapshot: 2,357 starts, 580 completions, 228 distinct papers, 580 distinct browser identities. Window: 11 Oct through 15 Nov 2026 IST, across exam types. These are recorded platform counts, not Quiz-1-only attempts or verified students. Starts include repeats. Completions exclude submissions after midnight on 16 Nov IST.

No runtime fetching, aggregation or polling. After Quiz 2, run this once with the new cutoff, then update the values and date labels together:

```sql
SELECT min(start_day) AS first_recorded_day, count(*) AS starts,
 count(completed_at) FILTER (WHERE completed_at < extract(epoch FROM timestamptz '2026-11-16 00:00:00+05:30')) AS completed,
 count(DISTINCT browser_key) AS browsers, count(DISTINCT paper_key) AS papers
FROM analytics_event WHERE start_day <= '2026-11-15';
```

## Prompts

Submitted exam results offer Give Feedback / Skip for Now. Active attempts, practice results and admin custom exams are excluded. Give Feedback focuses the existing form. Skip leaves results accessible and pauses feedback prompts for 24 hours. No repeat for the same attempt (last 30 IDs retained locally).

Successful feedback submission sets a local suppression flag. An indexed `contact_message.guest_hash` reconciles submissions associated with the current signed browser cookie. Known authors may see an optional support prompt at most once per seven days; feedback and support never stack. Payment checkout loads only after a click. Support is also available on the homepage, result page and footer.

Old reviews had no browser identity and cannot be retroactively attributed. Clearing cookies/site data or changing browsers can make a visitor unrecognizable. No fingerprint or email is collected to work around this.

Results no longer fetch the whole review wall in the background. `/feedback/state` is private and no-store, separate from shared cached reviews. The review list and its existing rating summary remain bounded to the latest 50 visible reviews.

## Hearts and migration

PUT/DELETE `/api/feedback/<id>/like` sets/removes the browser's like. Composite `(feedback_id,guest_hash)` primary key plus conflict-safe insertion prevents duplicates on retries. Hidden/non-feedback messages cannot be liked. CSRF, browser rate limits and IP limits apply. One grouped query gets counts for visible reviews; writes invalidate only `site-feedback`, preserving paper/catalog/solution caches.

Additive migration `8b33dd001011` adds one nullable indexed receipt column and a small likes table. PostgreSQL RLS is enabled on the new table, with public-role privileges revoked; Flask uses its existing server connection. Docker applies the migration before starting the new app. No question edits, ingestion changes, R2 objects, admin polling changes, cache-budget changes or worker-count changes. Point 6 stays deferred.

## Presentation refinement (16 Nov)

Keep only the topbar highlighted Notes link; remove the duplicate sidebar button and exam-row Notes card. Put lazy Support checkout buttons beside the homepage heading and result heading, retaining footer/result support access. The result heading always offers Give Feedback, including practice/custom results where automatic prompts are deliberately ineligible. Hearts use an unboxed, compact red outline/filled icon with count at each review card’s bottom-right.

The recap is platform-wide “MauryaHub in numbers”, no Quiz-1 label. Display conservative rounded-down milestones: 500+ estimated learner reach (browser-based), 2,300+ starts, 500+ completed tests and 200+ papers. Do not claim 3,000+ starts without supporting data. A single 850 ms count-up begins when visible, honors reduced motion and disconnects its observer/cancels its frame on unmount. The track is decorative animation, not a fabricated historical trend. No extra API calls or live count inflation.
