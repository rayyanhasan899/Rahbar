# Engineering notes

These answers describe the inspected implementation and observed evidence.
Cluster results still running are explicitly marked NOT VERIFIED; code locations
refer to the Day 3 dev tree. This is agent-assisted work, not a claim of personal
human debugging time.

## 1. Indexing during API startup

With three replicas, startup ingestion would create three competing writers to
one Chroma store, and every scale-out/restart would repeat ingestion. OCR and
embedding exceed the 60-second startup budget (k8s/base/api.yaml:53). Instead,
api/app/main.py:46 performs a bounded read-only pin check. The Job holds
writer_lock (indexer/pipeline/run.py:26,144), stages a new collection and publishes
only after count validation (indexer/pipeline/store.py:33,53). Manual Jobs and the
CronJob use the same shared PVC lock. ADR 0001 explains why Forbid alone is
insufficient. Cluster writer-wait/cutover evidence: NOT VERIFIED pending real audit.

## 2. Swapped liveness/readiness during a 90-second dependency outage

Liveness currently calls dependency-free /healthz; readiness calls /readyz,
which bounds Chroma/Redis operations (api/app/routes/health.py:18,23).
Swapping them would restart API containers after approximately three failed
20-second liveness intervals (k8s/base/api.yaml:60), while the always-healthy
readiness path would continue routing requests to broken readers. Startup load
would compound the outage. Correct readiness removes endpoints after its failure
threshold; liveness preserves processes. Recovery restores endpoints without
reindexing. Real outage/restart-count demonstration: NOT VERIFIED pending audit.

## 3. CPU HPA and generation latency

The required HPA uses 70% CPU with 3–8 replicas (k8s/base/hpa.yaml:18). The API
waits for Ollama over HTTP (api/app/providers/llm/ollama.py:32), so a saturated
model can produce high latency while API CPU remains low. More API readers do
not create model capacity. Requests in flight or p95 generation latency from
rahbar_generation_seconds are better demand signals through a metrics adapter;
model capacity must scale separately. Numeric HPA and `kubectl top` samples during a real
request: NOT VERIFIED pending audit. No invented scale-out is reported.

## 4. Indexer memory and limit

The real Job has a 1 GiB container limit (k8s/base/indexer-job.yaml:38). Extraction
is page-at-a-time, closes pdfplumber page layouts, caps Tesseract threads and
embeds in bounded batches. A local extraction process reached approximately
180 MiB in an observed sample; that excludes separate OCR child processes and
is not the Kubernetes indexer peak. The acceptance harness samples container
memory throughout the real Job. Peak, margin and timestamped container samples:
NOT VERIFIED until that artifact is inspected. An OOM kill conventionally exits
137 with reason OOMKilled; the laptop's old API-server exit 137 had
OOMKilled=false, so it is not evidence of an indexer OOM.

## 5. Recall by type

The pre-table-augmentation Day 1 experiment (eval/chunk-experiments.json) measured
11/13 recall@5 for all three configurations. Version questions were worst at
50%, ordinary 87.5%, exact/injection 100%. q09's clause 4.25 was displaced by
nearby 4.24/4.23; q08 retrieved equivalent handbook material outside the designated
reference label. The labels predate retrieval and remain unchanged. Do not claim
exact terms were worst merely because that is a plausible lecture example.
Fresh extraction/configuration and final generation results: NOT VERIFIED pending
the real audit, and must supersede this historical comparison before submission.

## 6. Changed embedding pin with old index

A new API checks the published pointer and collection model/dimension
(api/app/retrieval/chroma.py:30,68). A mismatch logs an index readiness conflict
(api/app/main.py:49), /readyz returns 503, and retrieval refuses a mixed-model
query. A ConfigMap edit alone does not replace an existing process environment;
the demonstration restarts the deployment. maxSurge 1/maxUnavailable 0
(k8s/base/api.yaml:88) allows old ready pods to serve while the new pod stays
0/1. Restore the prior pin or publish an index made with the new pin. Actual
conflict/recovery logs: NOT VERIFIED pending audit.

## 7. A failure lasting more than an hour

The Day 3 indexer Docker build spent 3888.2 seconds before failing in pip. Initial
working hypothesis was a cold large dependency download under a constrained
laptop/network; the final log instead showed an integrity mismatch:

```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
unknown package:
Expected sha256 fbde6962867ee75b48b0ee29b2b9372ec5d617799dbaf38e82dc0596f2f7738a
Got             6098eefdd749ff3a48013bbe8a12b70f18b930f33528c167eb2ce01997d47b23
```

The log did not identify the wheel or prove why its bytes differed. We did not
disable hash verification. A retry succeeded; subsequent work pins the complete
Python 3.12 wheel closure with official hashes and uses bounded retries/cache.
Actual command: docker build -t rahbar-indexer:day3 indexer. Raw local logs are
.venv/day3-indexer-build.log and .venv/day3-indexer-build-retry.log; the concise
committed excerpt is docs/evidence/day3-build-integrity-failure.txt. CI later
built and scanned all three images successfully. This is an observed agent-run
failure, not an invented hour of either partner's manual experience.

