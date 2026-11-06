# Web-service memory restart investigation

## Incident evidence

The supplied Render alert reports a memory-limit restart. The supplied log
excerpt shows Gunicorn starting at 2026-11-05 17:35:35 UTC (23:05:35 IST).
It does not identify the allocation or request that triggered the restart.
`GET 200 5232560` is 5.232560 seconds, because gunicorn.conf.py logs `%(D)s`;
it is not a response-byte count or memory reading. The slow analytics request
at 17:36:54 UTC is after startup and is not evidence that it caused the OOM.

The actual service plan, memory graph, complete pre-restart logs and deployed
environment overrides have not been inspected. No exact root cause is claimed.

## Changes prepared before deployment

- The process-local content cache now has an estimated Python-object byte
  budget as well as an entry-count limit. Oversized values are returned without
  retention; expired entries are purged on insertion. The budget is per worker
  and does not cap total process RSS or transient request allocations.
- Analytics starts at most the configured number of background writes. When
  saturated, the request performs the write synchronously instead of growing
  threads or an unbounded queue. This can add latency during bursts, but does
  not deliberately discard events. Existing best-effort write-failure behavior
  and potential daemon-write loss during process termination remain.
- One admin upload/workbook/PDF request runs per web worker. Overlapping requests
  receive HTTP 409 / PROCESSING_BUSY with Retry-After: 5, before claiming a job.
  Automatic missing-image repair shares this slot. Independent worker services
  and other web instances still need their own resource allocation.
- PDF processing and repair open files directly instead of retaining a full
  Python bytes copy beside MuPDF. Unused document-wide span collection was
  removed. OCR rasterization is capped at roughly eight million pixels, and its
  pixmap is released before Tesseract starts. Marker-color arrays are bounded
  to 256 x 256 pixels. Embedded images above sixteen million pixels fail that
  page's extraction with a warning; use a reduced-resolution source for those.
- Sampled logs include current process RSS, estimated cache bytes, cache entry
  count, thread count and route template. No request bodies, signed URLs or
  credentials are logged. Samples run on completed requests, so abrupt spikes
  can still occur between samples. RSS excludes other processes such as OCR.
- Gunicorn defaults to recycling after 10,000 requests plus up to 1,000 jitter.
  This is a safety net for gradual native-library growth, not proof of a leak
  and not protection against a single oversized request.

## Configuration for the existing service

render.yaml contains these defaults. A service created manually or with old
environment overrides may not adopt Blueprint values automatically. Check the
actual pyq_test-1 Environment and start command before deployment:

| Variable | Value |
|---|---:|
| WEB_CONCURRENCY | 1 |
| LOCAL_CONTENT_CACHE_BYTES | 33554432 (32 MiB estimated retained objects) |
| ANALYTICS_BACKGROUND_WRITES | 1 |
| MEMORY_LOG_INTERVAL_SECONDS | 60 |
| GUNICORN_MAX_REQUESTS | 10000 |
| GUNICORN_MAX_REQUESTS_JITTER | 1000 |

Keep the current request-thread count until production measurements justify a
change. More workers duplicate application/native-library/cache memory; setting
WEB_CONCURRENCY alone does not limit OCR or another separately hosted worker.
GUNICORN_CMD_ARGS or a custom start command can override repository settings.

## Local verification

A controlled cache-only comparison generated 128 synthetic papers, each with
40 unique long questions and four options. With an 8 MiB test cache budget:

| Cache version | Retained entries | Traced current Python allocations | Traced peak |
|---|---:|---:|---:|
| Previous count-only cache | 128 | 65.70 MiB | 65.70 MiB |
| Byte-bounded cache | 15 | 7.72 MiB | 8.27 MiB |

This measures synthetic cache allocations with tracemalloc, not production
RSS, traffic capacity or an expected service-wide percentage improvement.
Focused tests verify byte eviction, oversize bypass, TTL release, analytics
backpressure, processing-slot release after errors, bounded OCR pixels and
small marker arrays. Existing PDF extraction/scoring/storage tests also ran.

## Deployment validation still needed

Correlate Render memory percentage/limit with the few minutes before the
restart, including upload/catalog-processing activity and request traffic.
Check the actual worker count and any separate worker process sharing memory.
After deploying, compare memory_sample logs for normal browsing, exam starts,
analytics and one bounded catalog batch. Confirm ordinary extracted text,
diagrams, answer keys and processing retry behavior. Do not send a synthetic
traffic spike to the live student service to diagnose this incident.

Do not consider the OOM incident resolved until normal production workload
remains below its actual memory limit and the incident's activity is understood.
