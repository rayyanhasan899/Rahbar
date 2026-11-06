# Engineering notes

<!-- STARTER-TODO(7): answer all seven questions from section 7 of the case study, each
     pointing to your own files and line numbers. A generic answer scores zero. -->

Status: answers 1, 2, 3, 5 and 6 are drafted from the code and Day 1 measurements
on 6 November. Each still needs the cluster evidence named under it before
submission. Answers 4 and 7 need measurements and experience that do not exist yet.
Line numbers refer to commit dff9680 onwards; recheck them after later edits.

## 1. Indexing in API startup: what breaks with 3 replicas and one Chroma volume?

Three replicas would each ingest at start-up, so three writers would create
collections and move the active pointer at the same time against one Chroma
volume, and every restart or HPA scale-out would start another full ingestion.
Ingestion takes far longer than the start-up budget (`k8s/base/api.yaml:50-56`,
30 tries x 2 s = 60 s), so pods would be killed mid-write and loop.

What we do instead: the API only reads the published pointer at start-up
(`api/app/main.py:46`, `ChromaRetriever.active()` at
`api/app/retrieval/chroma.py:35`). The indexer is a separate Job and the only
writer, serialised by a file lock on a shared PVC (`indexer/pipeline/run.py:26-30`),
and it writes a staged collection that becomes active only after its count is
checked (`indexer/pipeline/store.py:33-55`). ADR 0001.

Evidence to add: Job and CronJob logs showing the lock, and an API pod log with no
ingestion lines.

## 2. Readiness and liveness swapped, Chroma slow for 90 seconds: what happens?

Swapped, liveness would call `/readyz`, which checks Chroma
(`api/app/routes/health.py:18-59`). After 3 failures 20 s apart
(`k8s/base/api.yaml:57-63`), about 60 s, the kubelet restarts every API container,
and keeps restarting them while Chroma is slow. That is a restart storm that adds
start-up load just as the dependency recovers. Readiness would call `/healthz`,
which always answers 200 (`health.py:13`), so the Service keeps sending traffic to
pods whose questions fail.

With the probes as configured, readiness fails after about 30 s
(`api.yaml:64-70`), the pods leave the Service endpoints, the Ingress returns 503
for those 90 s, nothing restarts, and the pods return to service on their own
once Chroma answers. A question that is already in flight gets a 503 with
"retrieval is unavailable" (`api/app/routes/ask.py:25-26`), not a 500 or an
invented answer.

Evidence to add: `kubectl get endpoints api -w` and restart counts while Chroma is
paused.

## 3. What does a CPU-based HPA measure on a generation service, and what should scale it?

`k8s/base/hpa.yaml` scales on 70% average CPU of the API pods. Generation does
not run in those pods: the API waits on an HTTP call to Ollama on the host
(`api/app/providers/llm/ollama.py`). While it waits, the pod's CPU stays low even
as requests queue and latency climbs, so the HPA sees little load. Adding API
replicas would not help anyway, because the bottleneck is the model server.

Better signals are requests in flight per pod or p95 generation latency
(`rahbar_generation_seconds`, `api/app/routes/metrics.py:26`) through a
Prometheus metrics adapter. Scaling to fix generation means scaling the model
server, which on our laptop is a single host process.

Evidence to add: `kubectl top` and HPA status during an evaluation run next to
`rahbar_generation_seconds`.

## 4. The indexer's peak memory, its limit, the margin, and the exit code when it is wrong

Pending: measure peak memory of the real-corpus Job (OCR pages included) and
record the limit, the margin and the OOMKilled exit code (137) from a deliberate
low-limit run. TEAM-PLAN task 16.

## 5. recall@5 by question type: where is it worst, and why?

Day 1 retrieval-only measurement (`eval/chunk-experiments.json`, all three chunk
settings): version questions 50%, ordinary 87.5%, exact and injection 100%.
Version is worst. q09 (2026 withdrawal deadline, clause 4.25) lost its slot to
neighbouring clauses 4.24 and 4.23 of the same document, which are about the
same subject and embed close to it. q08 found equivalent text in the student
handbook rather than the labelled clause. Exact terms did well because the
clause numbers appear verbatim in the chunks.

To redo with the final chunk size and the generation run (`eval/results.json`,
`by_type`) before submission.

## 6. EMBED_MODEL changed on the API only: what does your system do?

The API refuses to serve rather than query with vectors from the wrong model.
After a rollout restart, start-up logs "index readiness conflict"
(`api/app/main.py:49`) because the published pointer records the index's model
(`api/app/retrieval/chroma.py:42`). `/readyz` returns 503 with "published
embedding model mismatch" (`api/app/routes/health.py:44`). The new pods never
become ready, and with `maxSurge: 1` and `maxUnavailable: 0`
(`k8s/base/api.yaml:85-86`) the rollout stalls while the old pods keep serving.
A request that reaches a mismatched pod anyway gets a 503 from the same check in
`active()`.

Changing a ConfigMap does not restart pods by itself; the conflict shows on the
next rollout or restart. Fix by re-indexing with the new model or reverting the key.

Evidence to add: the pin-conflict demonstration (TEAM-PLAN task 13).

## 7. The failure that cost us more than an hour

Pending: each of us writes this from our own experience. Day 1's candidates are in
`docs/DAY1-REPORT.md` (Chroma's CHROMA_PORT service-link collision, cold-start
instability under CPU-based scaling).
