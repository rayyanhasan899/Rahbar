> FINAL OWNERSHIP UPDATE (22 November 2026): Rayyan has closed his project work allocation. All remaining tasks, including every historical Rayyan checklist item below, are assigned to Moez/his agent. See ../assignment-3/FINAL-HANDOFF-TO-MOEZ.md. This document is historical where it conflicts with that handoff/current runbook. Both members still must personally attend/explain.

# Assignment 03 (RAGOps) implementation plan

Course: CS4032 Software Construction and Development, Fall 26. Marks: 185.
Reference: Xu, Weytjens, Zhang, Lu, Weber and Zhu, *RAGOps: Operating and Managing
Retrieval-Augmented Generation Pipelines* (preprint, 2026). Figure 3 is the map.

Branch: `dev2` (from `main` at e92fbe7). Both members commit under their own identity
and review each other's pull request before `dev2` goes into `main`.

## The host machine

Every cluster run, measurement and demo happens on **Moez's laptop** (Windows, 16 GB
RAM, Docker Desktop on WSL 2, minikube, kubectl, Ollama with `nomic-embed-text` and
`llama3.2:3b`). Rayyan's 8 GB laptop could not hold generation in memory, so it is used
only for coding and offline tests.

Memory budget on 16 GB (keep the browser light during runs):

| Consumer | Budget |
|---|---|
| Windows + Docker Desktop VM overhead | about 4 GB |
| minikube node (`make cluster MINIKUBE_MEMORY=6144 MINIKUBE_CPUS=4`) | 6 GB |
| Ollama on Windows, llama3.2:3b loaded + nomic-embed-text | about 3.5 GB |
| headroom | about 2.5 GB |

If generation fails with an allocation error, close other apps first, then run
evaluations with fewer API replicas (`kubectl -n rahbar scale deploy/api --replicas=2`
after lowering the HPA minimum).

The Docker Desktop host address seen from minikube is `192.168.65.254` on this setup;
check it once (`minikube ssh -- getent hosts host.minikube.internal`) and pass it to
`scripts/deploy_local.py --provider-cidr <ip>/32 --ollama http://<ip>:11434`.

## Files in this folder

| File | Who reads it | What it is |
|---|---|---|
| PLAN.md | both | This overview: host, split, contracts, order of work |
| AI-TASKS-MOEZ.md | an AI assistant working for Moez | Code for Parts B, C, E and the release side of F |
| AI-TASKS-RAYYAN.md | an AI assistant working for Rayyan | Code for Parts A, D and the ingestion side of F |
| MANUAL-MOEZ.md | Moez | Hosting, every cluster run, screenshots, hand-written test data, report sections |
| MANUAL-RAYYAN.md | Rayyan | Hand checks, review, report sections, being on call for the A and D runs |

The AI files only describe code and manifests. Anything that needs the cluster, the real
model, a human judgement or a screenshot is in the MANUAL files. Every number in the
report must come from a run on our cluster, so no file here contains a measured value.

## Split

| Part | Owner | Runs on |
|---|---|---|
| B offline suite: golden set, three levels, stochasticity | Moez | Moez's laptop |
| C change experiment, release gate | Moez | Moez's laptop |
| E drift and coverage | Moez | Moez's laptop |
| F2 evaluation Job and gate ConfigMap, F3 candidate Deployment and rollout, F5 resources | Moez | Moez's laptop |
| A1 verification, A2 incremental update, Batch B | Rayyan (code) | runs on Moez's laptop |
| D1 to D5 traces, trace tool, metrics, guardrail logging | Rayyan (code) | runs on Moez's laptop |
| F1 data lake and traces volumes, F2 ingestion Job and CronJob, F4 traces on the cluster | Rayyan (code) | runs on Moez's laptop |
| G report | both | each writes the sections of their parts; G1, G2, G4(f) together |

Rayyan's code is built with fakes and unit tests on his laptop, pushed to `dev2`, then
Moez pulls, builds the images and runs it with Rayyan on a call. Both members read the
other's pull request line by line: each must be able to explain every part at the demo.

## Order of work

1. Moez: cluster up on his laptop with the Assignment 2 pipeline (README apply order).
2. In parallel: Moez builds the Part B suite, gate and coverage code against the current
   API; Rayyan builds Part A and Part D code with fakes.
3. Moez writes his hand golden questions, generates and reviews synthetic ones, runs the
   baseline suite twice (stochasticity).
4. Rayyan's A and D land on `dev2`; Moez rebuilds images and runs the ingestion Job on
   the real corpus, then Batch B (with Rayyan on a call); traces start flowing.
5. Part C: candidate collection (Rayyan's candidate ingestion Job), suite on candidate,
   gate, then F3 rollout and undo.
6. Part E: live queries, coverage, E3 after Batch B, E4.
7. D5 root cause from one Part B failure (Rayyan, from the trace Moez captures).
8. Screenshots, report, demo rehearsal on a fresh `minikube delete && make cluster`.

## Contracts between the two halves

### 1. What the suite needs from the API (exists already)

`POST /api/ask` returns `request_id`, `answer`, `citations`, `answered_from_context`,
`retrieved [{chunk_id, source, section, page, score}]` in rank order, and the
`X-Cache` header. `request_id` is also the trace id once Part D lands. The suite stores
it in every result row so D5 can open the trace of a failure.

The suite reads chunk texts for the faithfulness judge from Chroma by `chunk_id`, using
the pointer record `<CHROMA_COLLECTION>-control` / id `active` / `active_collection`.
Rayyan's incremental store must keep that pointer field.

### 2. Settings the suite needs (Moez adds them)

| Key | Where | Purpose |
|---|---|---|
| `SEED` | `rahbar-config` and API settings | passed to Ollama `options.seed`, for stochasticity runs |
| gate thresholds | `rahbar-gate` ConfigMap, mounted as `/config/gate.yaml` | Part C2 |

### 3. Candidate pipeline (Part C and F3)

The candidate is a chunking change, so it is a new collection: ConfigMap
`rahbar-config-candidate` with `CHROMA_COLLECTION=rahbar-cand` and the changed
`CHUNK_SIZE`/`CHUNK_OVERLAP`. `scripts/release.py` builds it with a Job made from the
`reindex` CronJob's own template, so whatever ingestion Rayyan's Part A ships is what
builds the candidate; his code must therefore refuse to reuse a collection built with
other settings, and must honour `CHROMA_COLLECTION`. The `api-candidate` Deployment reads
that ConfigMap. Release sets `CHROMA_COLLECTION` on the live `api` Deployment with
`kubectl set env`, which rolls out; `kubectl rollout undo` brings the previous
collection back.

### 4. What the API and ingestion side must provide (Rayyan)

- Data lake layout on a `datalake-data` PVC: current/, archive/<doc_id>/<version>/,
  quarantine/<run_id>/, reports/, state/<collection>/ledger.json.
- Chunk metadata adds `doc_id`, `doc_key`, `doc_sha256`, `archived`; the API filters
  `archived == false`.
- One trace record per query: stdout (logger `rahbar.trace`) and
  `/traces/traces-<pod>.jsonl`, with `trace_id` = `request_id`. Fields listed in
  AI-TASKS-RAYYAN.md.

### 5. Results and evidence folders (assignment requirement)

| Folder | Written by |
|---|---|
| `eval/results/` | suite, gate, coverage (Moez); ingestion reports copied from the PVC (Rayyan) |
| `traces/` | trace samples and summaries (Rayyan, copied on Moez's laptop) |
| `k8s/` | every manifest; `k8s/README.md` lists the apply order |

## Figure 3 mapping (draft for report table G1)

| Figure 3 stage | What RAHBAR does | File | Owner |
|---|---|---|---|
| Ingest | read incoming folders and their manifests | indexer/pipeline (Rayyan) | Rayyan |
| Verify | quality, completeness, recency, uniqueness | indexer/pipeline (Rayyan) | Rayyan |
| Update data lake | current/archive/quarantine, ledger | indexer/pipeline (Rayyan) | Rayyan |
| Update retrieval sources | incremental chunk/embed/delete/archive | indexer/pipeline (Rayyan) | Rayyan |
| Offline testing | three-level suite | eval/suite.py and its modules | Moez |
| Live testing | traces, metrics, gated rollout | api (Rayyan), k8s/candidate, scripts/release.py (Moez) | both |
| Check coverage | live queries against the golden set | eval/coverage.py | Moez |

The "what is missing" column is filled in after the runs.
