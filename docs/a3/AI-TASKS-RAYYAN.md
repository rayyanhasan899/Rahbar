# AI tasks for Rayyan: Parts A, D and the ingestion side of F

Give this file and `docs/a3/PLAN.md` to the AI assistant. Branch `dev2`, one commit per
working feature, author Rayyan. The contracts in PLAN.md are fixed; change them only
with Moez's review. Rayyan's laptop does not run the cluster: build and test with fakes
(`make test`, `make lint`), push, and Moez runs it on his laptop.

Rules for the assistant:

- No invented numbers; scripts write reports, the report quotes the files.
- Repository style: Python 3.12, ruff line length 100, mypy clean, tests with fakes (no
  network, no model, no cluster).
- Plain `print("label", value)` for console output, no f-string prints.
- Do not edit `eval/` (Moez's suite) without telling Moez.

## A1. Verification stage

New module (for example `indexer/pipeline/verify.py`) that runs after extraction and
before chunking. One result per document with four checks, each
`{"passed": bool, "reason": str}`:

| Check | Rule |
|---|---|
| quality | extraction succeeded; enough letters/digits (`MIN_TEXT_CHARS`); not garbled (printable and letter ratios, replacement characters) |
| completeness | title, source, version and page count present; declared `pages` equals extracted pages; PDF ends with `%%EOF`; a text document does not stop mid-sentence |
| recency | no newer version of the same `doc_id` (document family) is known; a rollback pin wins |
| uniqueness | no exact duplicate (sha256); no near-duplicate (cosine of document embeddings at or above `NEAR_DUP_THRESHOLD`, against documents of another `doc_id`) |

Outcomes: accepted, unchanged, archived (only recency failed), quarantined (anything
else). Quarantined files are copied to `/datalake/quarantine/<run_id>/` with a
`.reason.json`; they are never chunked. A changed document that fails keeps its
previous verified version. Report per run: `/datalake/reports/verification-<run_id>.json`
plus a table in the Job log. A `--verify-only` mode writes the report without touching
the index (to read the closest cosine values before fixing the threshold).

Metadata comes from `_index.json` (corpus/fetch.py, which must copy `doc_id` from
`corpus/sources.yaml`), Markdown front matter, or PDF metadata. The 2023 and 2026
academic rules share `doc_id: academic-rules`. CI fixtures in `eval/fixtures/` need
`title` and `doc_id` in their front matter, or CI breaks.

## A2. Incremental update

- One long-lived collection `<CHROMA_COLLECTION>-data` and a ledger
  `state/<collection>/ledger.json` in the data lake (document key, doc_id, version,
  sha256, status, chunk ids).
- Unchanged bytes and status: skipped, 0 chunks embedded (document embeddings and
  extraction cached by sha256, so nothing is re-read or re-embedded).
- Changed bytes: delete that document's old chunk ids, embed and add the new ones.
- Status change only (archived by a newer version, rollback): metadata update.
- Active document missing from every incoming folder: chunks deleted by `doc_key`,
  lake copy moved to the archive.
- After every run compare chunk counts per document in Chroma with the ledger; any
  orphan fails the Job. Repair a run that died half way on the next run.
- Keep the pointer `<collection>-control` / `active` with `active_collection`,
  `generation`, `embed_model`, `dimension` (the API and Moez's suite read it); add
  `embed_model_digest` (from Ollama `/api/tags`) and `chunk_size`. Move `generation`
  only when the retrievable chunks change.
- A ledger built with another embedding model or chunking refuses to be updated: that is
  a new `CHROMA_COLLECTION` (Moez's candidate depends on this).
- `python -m pipeline.rollback --doc-id X --version V` and `--unpin X`;
  `python -m pipeline.counts` prints chunks per document, active and archived.
- API: always filter `archived == false`; a question naming a year only narrows to active
  versions of that year (agreed: archived versions are never retrieved).

## Batch B

At least 10 synthetic documents, labelled as test data, in `corpus/batch-b/` with an
`_index.json` (sha256 per file, for `scripts/corpus_transfer.py`): 2 exact duplicates,
1 near-duplicate, 1 truncated PDF, 1 corrupt PDF, 1 missing metadata, 1 garbled, 1 newer
version of an existing document, 1 injected instruction, clean ones. `EXPECTED.md` maps
each problem to the check that should catch it. A generator script keeps it
reproducible. `scripts/corpus_transfer.py --source <dir> --dest <subfolder>` copies a
batch into the corpus PVC (keep `deploy_local.py` working: it calls the transfer
function).

## D1, D2, D4. Trace record and trace tool

One record per `/api/ask`, to stdout (logger `rahbar.trace`) and, when `TRACE_DIR` is
set, to `TRACE_DIR/traces-<HOSTNAME>.jsonl`. `trace_id` equals the response's
`request_id`. Fields: `trace_id`, `ts`, `query`, `rewritten_query`,
`embedding {model, digest}`, `collection {name, active_collection, generation}`,
`filters`, `retrieved [{rank, chunk_id, doc_id, source, section, page, doc_version,
score, text}]`, `reranked_order`, `prompt_sha256`, `prompt` (messages of the last model
call), `model {provider, name, temperature, num_ctx, num_predict, seed}`,
`response {answer, answered_from_context, confidence}`, `citations`,
`guardrails {question_flagged, passages_neutralised, sentences_removed,
below_relevance_floor, citation_retries, fallback, actions[]}`,
`latency_ms {embed, search, guard, generate, total}`, `cache {result, similarity}`.

A trace write failure must never fail the answer. `scripts/trace_tool.py show <id>
[paths|-]` prints the context and the exact prompt and verifies the prompt hash; it reads
trace files, folders, or `kubectl logs` on stdin. D4: the injection guard's actions go
into `guardrails.actions`.

Note: Moez adds a `SEED` setting to the API and Ollama provider for Part B. Include
`seed` in the trace's `model` block once that lands (coordinate the merge).

## D3. Metrics

Prometheus: top-1 similarity histogram, per-stage latency histogram, query counter
(abstention rate = abstentions / queries); the cache and injection counters exist.
`scripts/trace_summary.py --since --until` over trace files: top-1 similarity
distribution, abstention rate and reasons, cache hit rate, p50/p95 per stage, injection
attempts flagged.

## F1, F2, F4. Ingestion on Kubernetes

- PVCs `datalake-data` (1Gi) and `traces-data` (256Mi, ReadWriteOnce is fine on
  minikube's single node).
- Indexer Job and weekly CronJob mount `/datalake` read-write and `/corpus` read-only;
  they hold the writer lock, so they are the only writers to Chroma.
- ConfigMap keys `DATALAKE_DIR`, `INCOMING_DIRS`, `NEAR_DUP_THRESHOLD`,
  `MIN_TEXT_CHARS`, `TRACE_DIR`.
- `k8s/jobs/`: rollback Job, verify-only Job, a read-only data lake shell Pod
  (label `app: indexer` so the NetworkPolicy lets it read Chroma).
- `k8s/candidate/ingest-job.yaml`: the ingestion Job using
  `rahbar-config-candidate` (Moez creates that ConfigMap in `k8s/candidate/`).
- API Deployment mounts `traces-data` at `/traces`.
- Keep `scripts/deploy_local.py` working: it picks the first `Job` in the base
  kustomization, so one-off Jobs stay outside `k8s/base`.
- `k8s/README.md`: the Part A and D commands.

## Changes that touch Moez's side (tell him)

- `scripts/real_cluster_checks.py` (Assignment 2 audit) expects every reindex to change
  the generation; with A2 an unchanged re-run keeps it on purpose.
- Golden q10 (2023 rules) becomes unanswerable; Batch B's newer document archives the
  document it replaces, which is the drift Moez reports in E3.
