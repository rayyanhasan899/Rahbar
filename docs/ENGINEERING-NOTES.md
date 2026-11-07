# Engineering notes

These answers describe the inspected implementation and observed evidence.
Remaining cluster results are explicitly marked NOT VERIFIED; code locations
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
insufficient. Actual source-54f37ff Job published 646 chunks independently of
API startup (docs/evidence/day3-audit-54f37ff/indexer.log). The corrected audit (4917e45) then proved live cutover with 47 HTTP-200
question probes, unchanged API template, a new generation at the same 646 count,
a MISS across publication followed by HIT, and a manual writer waiting 208.441 s.
See docs/evidence/day3-audit-4917e45/reindex.json and manual-lock.log.

## 2. Swapped liveness/readiness during a 90-second dependency outage

Liveness currently calls dependency-free /healthz; readiness calls /readyz,
which bounds Chroma/Redis operations (api/app/routes/health.py:18,23).
Swapping them would restart API containers after approximately three failed
20-second liveness intervals (k8s/base/api.yaml:60), while the always-healthy
readiness path would continue routing requests to broken readers. Startup load
would compound the outage. Correct readiness removes endpoints after its failure
threshold; liveness preserves processes. Recovery restores endpoints without
reindexing. The real audit held Chroma down for at least 90 seconds: /healthz
stayed 200, /readyz returned 503, API UID/restart counts were unchanged and
readiness recovered. Evidence: docs/evidence/day3-audit-54f37ff/dependency-probes.json.
The swapped configuration is a causal analysis; it was not actually deployed.

## 3. CPU HPA and generation latency

The required HPA uses 70% CPU with 3–8 replicas (k8s/base/hpa.yaml:18). The API
waits for Ollama over HTTP (api/app/providers/llm/ollama.py:32), so a saturated
model can produce high latency while API CPU remains low. More API readers do
not create model capacity. Requests in flight or p95 generation latency from
rahbar_generation_seconds are better demand signals through a metrics adapter;
model capacity must scale separately. Four actual `kubectl top`/HPA snapshots
during a real follow-up recorded 19%, 9%, 9%, 9% CPU utilization, below the 70%
target; the final snapshot was numeric at 1%. The real follow-up was cited and
answered by Ollama. Three distinct endpoint IPs were present. See
docs/evidence/day3-audit-54f37ff/resources.json and metrics.txt. No scale-out
is invented; this small observation supports the CPU-signal limitation.

## 4. Indexer memory and limit

The real Job has a 1 GiB (1024 MiB) container limit and 256 MiB request
(k8s/base/indexer-job.yaml:35,38). Extraction closes PDF page layouts, limits
Tesseract threads and embeds in bounded batches. The real container was sampled
64 times, nominally every three seconds, during indexing. Highest observed memory
was **203 MiB** at 21:22:55–21:23:07 UTC on 6 November (02:22:55–02:23:07 PKT on
7 November); margin to the limit was **821 MiB**, about 80.2% of the limit.
These are container samples including OCR children, not only a Python process.
See docs/evidence/day3-audit-54f37ff/indexer-top.log:58 and indexer.log. A brief
unsampled peak could be higher. The 1 GiB limit intentionally retains headroom
for page rasterization; this corpus measurement does not establish arbitrary-PDF
memory safety. The Job completed without an observed OOM.

If cgroup memory exceeds its limit, Kubernetes reports reason OOMKilled and exit
137; examine `kubectl describe pod` and container lastState, not just the number.
No deliberate indexer OOM experiment was performed. The laptop's old API-server
exit 137 had OOMKilled=false and is not indexer OOM evidence.

## 5. Recall by type

The fresh real-corpus final measurement (eval/results.json, source 54f37ff)
reports version questions worst at **50%**, ordinary **87.5%**, exact and
injection **100%** recall@5. Overall is **11/13 = 84.6154%**, with absent-topic
questions excluded from recall. The fresh three-configuration experiment agrees.
q09's designated clause 4.25 loses its slot to nearby clauses/table sections;
q08 retrieves equivalent handbook material outside its designated reference.
For q09 the model can still answer from a table, but recall correctly does not
rewrite the predeclared clause label to count that as a hit. The JSON retains
per-question references for inspection. Exact terms were not worst in this small
set. Nine questions received cited model answers; four non-mandatory cases safely
refused/fell back. Retrieval recall and answer availability measure different
things; 100% citation validity is not a claim of complete factual correctness.

## 6. Changed embedding pin with old index

A new API checks the published pointer and collection model/dimension
(api/app/retrieval/chroma.py:27,65). A mismatch logs an index readiness conflict
(api/app/main.py:49), /readyz returns 503, and retrieval refuses a mixed-model
query. A ConfigMap edit alone does not replace an existing process environment;
the demonstration restarts the deployment. maxSurge 1/maxUnavailable 0
(k8s/base/api.yaml:88) allows old ready pods to serve while the new pod stays
0/1. Restore the prior pin or publish an index made with the new pin. Actual
conflict/recovery logs are in docs/evidence/day3-audit-54f37ff/pin-conflict.json:
new pod api-7545dfdb7d-b8242 stayed unready and logged index=nomic-embed-text
api=deliberately-wrong-model. Restoring the original configuration recovered the
publication with 646 chunks and the original model. The audit waits for Running
before reading the conflict logs, so ContainerCreating is not mistaken for failure.

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

The corrected full audit at source 4917e45 passed. Its initial Job had 66 memory
samples, with highest observed 160 MiB (864 MiB limit margin); the earlier real
run's 203 MiB remains the larger observed peak across these two runs. Rollback
now verifies status 200 and exact original UI bytes, rather than absence of a
demo marker in an error page. Source/comment-only documentation edits after this
audit do not alter the tested application, pipeline or manifests.
