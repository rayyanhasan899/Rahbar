# Assignment 3: exactly three implementation phases

Owner: Rayyan Hassan. Prepared 22 November 2026. Planning only.
Execution updates: [Phase 1 report](phase-reports/PHASE-1-REPORT.md) and
[shared ledger](COMMUNICATION.md). This task catalogue remains the planning baseline.
Read README.md, ASSIGNMENT-3-GAP-ANALYSIS.md and COMMUNICATION.md first.
Official five-page Assignment_03.pdf controls; partner plans are proposals, not proof.

## Operating contract

Use the existing RAHBAR system and Moez's dev2 work. Do not implement against local
dev's older A2 files and overwrite newer features. The inspected dev2 head is
3dff73646eaf17ee778a2512f1e1d51166a59ebe; re-inspect before each future phase.
Keep original commits/authorship, source provenance, active-collection pointer,
model compatibility, one writer, validated answers, guarded cache, security and CI.

Every task below is mandatory assignment work or a justified fix required for a
mandatory path. Optional additions (authentication, new UI framework, alternative
database, cloud migration, novel reranker, production telemetry platform) are excluded.

Task ownership means delivery responsibility, not a claim of manual authorship.
Rayyan's agent executes his feasible engineering work end-to-end. Human-only and
inaccessible-host work is assigned explicitly in COMMUNICATION.md, not silently omitted.
Commit with Rayyan's verified identity when authorized. Preserve actual AI disclosure.

## Remaining task catalogue

### T01 - Reconcile implementation and freeze additive interfaces
- Requirements: A1/A2, D1/D2, F2/F3; A2 safety carried forward.
- Why/status/evidence: plan exists, but in-place deletion, recency outcomes,
  historical filtering and reader/writer promotion conflict (gap analysis items 7-10).
- Inspect: docs/a3/*.md, indexer/pipeline/{run,store,models,config}.py,
  api/app/{schemas,config}.py, retrieval/chroma.py, eval/common.py, scripts/release.py.
- Expected edits: communication decisions and an A3 design ADR/contract document;
  minimal additive schema/config changes in later tasks.
- Dependencies: current dev2 inspection; Moez coordination on breaking assumptions.
- Complexity High; priority Critical; independent additive exploration is safe,
  shared contract changes require coordination. Ownership: joint, not all Rayyan.
- Accept/test: stable doc identity/version/hash definitions; pointer compatibility;
  unchanged-run and failure semantics specified; no existing field removed silently.

### T02 - Four-check document verification and quarantine
- Requirements: A1.
- Why/status/evidence: no verification/report stage; extraction currently feeds chunking.
- Inspect/change: indexer/pipeline/{run,extract,models,config}.py; add verify.py
  and focused tests under indexer/tests/; extend corpus manifest metadata.
- Dependencies: T01 document/metadata contract.
- Complexity High; priority Critical; Rayyan-owned, largely independent.
- Accept/test: each input gets four pass/fail-with-reason records (quality,
  completeness including truncation/required metadata, recency, hash/embedding
  uniqueness). Catch extraction failures per document; failed inputs never reach
  chunk/embed and receive durable quarantine/report artifacts. Distinguish accepted
  historical archival from failed incoming data. Test malformed PDF/manifest/text,
  absent title/date-or-version/pages, duplicate and near-duplicate thresholds.

### T03 - Persistent incremental ledger, deletion reconciliation and rollback
- Requirements: A2, F1/F2.
- Why/status/evidence: run_pipeline embeds all documents; staged publication is not A2.
- Inspect/change: pipeline/{run,store,embed,models,config}.py; add ledger/data-lake,
  reconciliation, counts and rollback modules as warranted by existing architecture.
- Dependencies: T01/T02; collection-specific configuration fingerprints.
- Complexity High; priority Critical; Rayyan-owned; coordinate pointer with Moez.
- Accept/test: unchanged rerun zero embedding calls/chunks, stable generation when
  nothing retrievable changes; changed document only refreshes its own content;
  deleted document has no orphan chunks by doc_id; archive excluded from live
  retrieval and restore/unpin works. Cache near-duplicate embeddings by content/config
  too, so unchanged verification does not hide re-embedding costs.
  Preserve last valid content on invalid update; interrupted replacement recovers
  without a mixed or empty live index; shared lock covers manual and scheduled Jobs.
  Test candidate collection isolation/model or chunking mismatch rejection.

### T04 - Reproducible owned Batch B and transfer integration
- Requirements: Batch B, A1/A2, D4, E3.
- Why/status/evidence: absent on inspected dev2.
- Inspect/change: corpus/batch-b/ (new), generator, EXPECTED.md, _index.json;
  scripts/corpus_transfer.py and pipeline discovery only as needed.
- Dependencies: T02/T03 metadata/identity contract.
- Complexity Medium; priority High; Rayyan-owned, coordinate golden scenarios.
- Accept/test: >=10 owned documents, >=2 exact duplicates, near duplicate,
  truncated/corrupt input, missing metadata, newer policy version, injected instruction.
  Manifest hashes match generated files, expected outcomes are explicit.
  Keep a valid injection-bearing document reachable to test the retrieval guard;
  do not simply quarantine every injected document and claim D4 passed.
  Transfer remains compatible with deploy_local.py. No third-party PDF committed.

### T05 - Complete request traces and exact replay tool
- Requirements: D1/D2/D4, F4.
- Why/status/evidence: partial stdout logs lack required trace/provenance/persistence.
- Inspect/change: api/app/{main,schemas,config,logjson}.py,
  services/{answer,guard,cache}.py, retrieval/chroma.py, providers/llm;
  add trace service and scripts/trace_tool.py; tests under api/tests/.
- Dependencies: T01/T03 document IDs/model digest and pointer contract.
- Complexity High; priority Critical; Rayyan-owned with shared API coordination.
- Accept/test: one terminal trace record per query including cache hits, refusals
  and failures; required query/rewrite, model/version, collection/generation,
  ranked chunks/doc IDs/versions/scores/text, filters/order, exact prompt/hash,
  model parameters/seed, response/citations, rail actions, stage timings/cache state.
  Record sanitized context actually sent, retry prompts and original cache provenance.
  Trace ID equals request_id; output JSON stdout plus durable pod-specific JSONL.
  Trace writer failure must not crash answer handling but must be detectable.
  Tool reconstructs actual context/prompt and verifies hash after source deletion
  or reindex; redacts credentials. No invented LLM call for cache hits.

### T06 - Trace summaries, distributions and diagnostic contract
- Requirements: D3/D5, F4.
- Why/status/evidence: existing counters do not provide all required distributions/
  per-stage p95 or a time-window trace summary.
- Inspect/change: api/app/routes/metrics.py, trace instrumentation;
  scripts/trace_summary.py; pure unit tests.
- Dependencies: T05 trace schema and clock/unit semantics.
- Complexity Medium; priority High; Rayyan-owned, D5 depends on a real Part B run.
- Accept/test: top-1 distribution, abstention/cache rates, stage p50/p95 and injection
  counts over explicit time windows; handle zero denominators/missing stages and
  distinguish cache bypass from miss. Test boundaries and mixed error/hit/refusal rows.
  D5 remains pending until Phase 3 chooses a real failed/abstained answer and produces
  five evidence-grounded lines using only its trace.

### T07 - Persist data/trace lifecycle and run it as Jobs
- Requirements: F1/F2/F4 and ingestion side of F5.
- Why/status/evidence: existing corpus PVC read-only; no data-lake or trace PVC.
- Inspect/change: k8s/base/{api,indexer-job,reindex-cronjob,configmap,
  networkpolicy,kustomization}.yaml; add data/trace PVCs and separate one-off
  verify/rollback inspection Jobs outside base; k8s/README.md; deploy_local.py.
- Dependencies: T02/T03 for ingestion mounts; T05 for trace mount.
- Complexity Medium/High; priority Critical; Rayyan-owned, shared manifest coordination.
- Accept/test: persistent current/archive/quarantine/reports/ledger; API trace volume;
  non-root/read-only-root retained with scoped writable mounts; Job-only Chroma writer;
  writer lock works across manual Jobs; API startup never indexes.
  Preserve first-base-Job assumptions in deploy_local.py.
  Render/strictly validate all new objects, then prove persistence in Phase 3.

### T08 - Valid golden set, manual provenance and workload datasets
- Requirements: B golden/judge agreement, E1/E4, submission honesty.
- Why/status/evidence: golden_check currently returns 34 issues; no live/hand labels.
- Inspect/change: eval/golden.jsonl, synthetic candidates, hand_labels.jsonl,
  live_queries.jsonl, embedding-pairs.jsonl and golden_check tests with Moez.
- Dependencies: T04 Batch B scenarios and actual source pages; start human requests early.
- Complexity Medium; priority Critical; both members, Moez owns eval integration.
- Accept/test: >=25 questions, >=15 answerable with verified physical pages,
  >=5 unanswerable, >=5 hard; >=8 actually human-written; >=8 synthetic actually
  human-reviewed. >=8 answers human-labelled before viewing judge results.
  >=40 live-style queries/about28 in-domain and >=12 uncovered; later add >=6
  distinct golden questions. Label AI drafts synthetic and preserve data revisions.
  Run golden_check before expensive service calls; never self-certify human review.

### T09 - Harden partner suite, gate, release and CI integration
- Requirements: B/C/E, F2/F3; preserve A2 regressions.
- Why/status/evidence: partner modules exist; concrete risks listed in gap analysis.
- Inspect/change with Moez: eval/{suite,common,job,gate,coverage,end_to_end}.py,
  tests, gate.yaml, k8s/eval/, candidate/, scripts/release.py, Makefile,
  Dockerfiles and .github/workflows/ci.yml.
- Dependencies: T03/T05 exact-evidence interface and T08 valid inputs.
- Complexity High; priority Critical; shared/Moez-led; announce scoped edits first.
- Accept/test: golden validated before HTTP; finite bounded thresholds and meaningful
  missing/no-citation handling; explicit immutable baseline and comparable runs;
  exact judged context; seeded/cache-isolated measurements; no coverage import clash;
  candidate gate fails without live rollout; promotion/undo keep reader and scheduled
  writer configuration coherent. New eval image and standalone manifests are checked
  by CI on intended dev2/PR paths. Keep model services mocked in offline tests.
  Stop interpreting null thresholds as a coding defect: fill from Phase 3 measurements,
  with a written rationale, then demonstrate threshold editing without rebuilding.

### T10 - Run the complete measured Kubernetes evidence sequence
- Requirements: A/B/C/D/E/F runtime clauses and F5.
- Why/status/evidence: no committed A3 run evidence identified.
- Inspect/change: results/traces/evidence outputs; calibrated configs and resource
  settings only when justified; source fixes go back through tests/review.
- Dependencies: T01-T09 integrated; host access/HM requests in communication file.
- Complexity High; priority Critical; Moez host, both members involved.
- Accept/test: full sequence in Phase 3 below, actual raw result files committed;
  no fabricated metrics/screenshots or cached stochasticity runs.

### T11 - Produce the final report and exact submission package
- Requirements: G1-G5 and Submission.
- Why/status/evidence: draft plan tables are not final report; no submission PDF.
- Inspect/change: report source/PDF in agreed docs location, docs/AI-USAGE.md,
  README.md A-F commands, k8s/README.md, evidence indexes and result manifests.
- Dependencies: T10 actual outputs and confirmed paper, names/roll numbers.
- Complexity Medium; priority High; both, automation can prepare/render.
- Accept/test: <=8 main pages, names/roll numbers first page, all G tables and six
  findings-based answers, true contribution table and 2-3-line AI statement;
  labelled uncropped own-terminal screenshots appendix. Render/visually inspect PDF.
  No private keys or source documents without rights.

### T12 - Clean-cluster rehearsal, review and delivery checks
- Requirements: fresh cluster, Kubernetes demo, repo results and both contributors.
- Why/status/evidence: A2 rehearsal is not proof of A3.
- Inspect/change: documentation/evidence fixes only as needed; no checker weakening.
- Dependencies: T10/T11 and actual partner reviews.
- Complexity Medium; priority Critical; joint; destructive cluster actions need
  specific authorization or use a separate named disposable cluster.
- Accept/test: clean checkout can apply documented objects and answer/abstain;
  live eval Job, trace tool and unseen batch ingest succeed; rollback yields a new
  trace with previous collection/model version; both can explain all parts.
  Reviewed PRs/checks, pushed results/traces/manifests, final PDF accessible;
  no Classroom submission unless separately instructed.

## Phase 1 - Verified incremental data lifecycle

Objective: A1/A2 and Batch B work with safe storage semantics and fake tests; the
ingestion-side Kubernetes manifests are ready for later integration.

Order: T01 -> T02 -> T03 -> T04 -> ingestion portion of T07.
Send T08 human-data and host requests immediately; do not wait until Phase 3.
Scope files: indexer/pipeline, indexer/tests, corpus Batch B generator/fixtures,
corpus metadata/transfer, data-lake PVC, Job/CronJob mounts and ingestion docs.
Coordinate but do not replace Moez's eval/release implementations.

Acceptance: four checks and quarantine report; cached unchanged verification and
zero chunk embeddings; changed/deleted counts; archive/restore; invalid-update
preservation; shared writer lock; crash/recovery and collection-isolation tests;
owned Batch B; no API-startup ingestion. Trace schema contract is specified, not
implemented yet. Record every test command and actual result.

Validation (existing inspected Python3.12 environment, no external services for unit tests):
- source .venv/rahbar-env.sh on the prepared WSL laptop; inspect before sourcing/changing.
- cd indexer && python -m pytest tests -q
- ruff check indexer corpus scripts
- cd indexer && mypy pipeline
- python -m pytest eval/tests -q for transfer/contracts touched after coordination.
- kubectl kustomize k8s/overlays/prod, then existing strict kubeconform tooling.
Use a distinct disposable data/test directory. Never run the actual indexer against
live volumes just to test idempotence.

Risks/rollback: bad dedup threshold, identity collisions, deletion scope and unsafe
ledger/vector ordering. Retain old publication/data, configuration fingerprint and
recovery journal until replacement validates. Use a normal revert PR if needed,
never reset/clean or erase user corpus.
Definition of Done: code/tests/docs and ledger updated, required checks passing or
honestly blocked with commands/evidence; isolated Rayyan-authored milestone commits/
pushes/PR prepared as authorized; no Phase 2 automatically started.

## Phase 2 - Traceability and integration correctness

Objective: D1-D4 plus trace/metrics F4 integrate with the completed A layer and
Moez's B/C/E/F release code. Resolve T08/T09 issues without duplicating partner work.

Order: confirm Phase1 -> T05 -> T06 -> remaining T07 -> T08/T09 jointly.
Request real failure trace for D5; do not write its conclusion before a real run.
Scope files: API services/providers/retriever/schemas/config, trace tools/tests,
trace PVC and manifests; narrowly coordinated eval/gate/release/CI fixes.
Keep seed support, active pointer, Answer/AskResponse compatibility and guarded cache.

Acceptance: exact prompt reconstruction across retries/hits/errors; durable JSONL,
safe degraded trace-write behavior; correct summaries/metrics; archived live filtering
and candidate isolation; valid golden and truthful human provenance or explicit block;
finite fail-closed gate, explicit baseline, reader/writer coherent release/undo;
new image/manifests/tests covered in CI.

Validation:
- cd api && python -m pytest tests --cov=app --cov-fail-under=60 -q
- cd indexer && python -m pytest tests -q
- python -m pytest eval/tests -q
- python eval/golden_check.py
- ruff check api indexer eval corpus scripts
- cd api && mypy app; cd indexer && mypy pipeline
- python -m pip check
- Render and strictly validate production AND separate eval/candidate/jobs manifests.
- Build/scan all four images where authorized; use existing locked dependencies.
Unit tests must not contact external models/services; fake trace logs for pure tools.
Real runtime outcomes are not a prerequisite to call offline code implemented, but
are a prerequisite to call the corresponding assignment requirement complete.

Risks/rollback: mismatched evidence generations, trace secrets/disk pressure, seed/cache
contamination and coupled release configs. Preserve old response fields, apply additive
changes, retain immutable baseline/results and old model/collection configuration.
Definition of Done: integration defects resolved/tested, communication decisions
recorded, CI/checks and no-overwrite review completed; outstanding human/host actions
explicit. Stop without launching Phase3.

## Phase 3 - Measured Kubernetes evidence and submission

Objective: demonstrate A-F with own pipeline runs, complete D5/G and a reproducible
submission. This is actual execution and report preparation, not invented values.

Order:
1. Verify host/context, branch/image SHAs, paper/due date and golden provenance.
   Use Moez's approved machine/access. Do not change host settings silently.
2. Build four images and apply dependencies/PVCs/configs/policies, verified ingestion,
   then API readiness. Record image/model digests and corpus/golden hashes.
3. Run Batch A then unchanged A (zero embed), changed/deleted/count reconciliation,
   archive/rollback; run Batch B verification/incremental update; prove PVC survival.
4. Establish a deliberately selected baseline and run full B twice with fixed seeds
   and cache isolation. Compute module metrics, all retrieval metrics, noise deltas,
   faithfulness/abstention/citations/latency and >=8-human-label judge agreement.
5. Choose exactly one C pipeline change. Compare all three levels on equivalent
   datasets. Calibrate/justify thresholds, demonstrate fail/pass and ConfigMap-only
   outcome change. Never modify the baseline just to pass.
6. Prove distinct candidate/live collections and Services; failed candidate does not
   roll out. Promote passing candidate, then controlled bad release/undo; obtain a new
   trace with restored collection AND embedding version; verify scheduled writer too.
7. Verify D trace stdout/file persistence, trace reconstruction, metrics forwarding,
   time-window summary, Batch B guard action; write D5's five lines from trace only.
8. Run E coverage with >=40 live queries; justify similarity/share thresholds,
   list topics, compare suite after B drift, add >=6 questions, show increased
   coverage and below-threshold nonzero exit.
9. Measure API/vector-store/ingestion/eval resources; set justified requests/limits.
   Capture every required raw uncropped terminal screenshot with command/output.
10. T11 report and T12 clean-cluster/unseen-batch rehearsal; final reviews/pushes
    and report/package links. Do not submit a form unless separately requested.

Acceptance: evidence files under eval/results/ and traces/, all manifests under
k8s/, exact commands for A-F, all mandatory screenshots and G sections, <=8-page
main report, actual member contributions/AI statement. Do not use A2 evidence as
if it demonstrated new A3 behavior.

Validation: rerun Phase2 quality commands after fixes; actual eval Job exits with
gate outcome; strict validation/build/scan all new objects/images; unchanged submission
checker as an A2 regression lint (not an A3 grader); clean-clone commands on a separate
disposable cluster when approved. Check baseline/results provenance and screenshot/PDF
legibility. Have both members explain each other's code and run the demo sequence.

Risks/rollback: destroying a user's cluster, losing evidence, nonfinite/nullable
measurements, false faithfulness claims, cache-warmed latency, absent human inputs.
Use separate named cluster/volumes, save before/after config and raw outputs, preserve
previous revisions, never force-push, never delete the existing project data.
Definition of Done: every official item has concrete implementation+verification
evidence or is explicitly BLOCKED/NOT VERIFIED. No broad completion declaration
with missing human work, screenshots or inaccessible host. Stop after reporting
submission readiness; no further feature phase.

## Branch strategy for future authorized implementation

No branches are created now. Recommended: inspect/fetch normally, preserve the
untracked guide, use an isolated codex/a3-phase-1 branch from current dev2; subsequent
feature branches start from the reviewed integrated dev2. Open PRs targeting dev2.
Coordinate CI triggers for that base. Only a genuinely approved, passing final
dev2 PR can merge into main. If protection requires human review, wait for it;
do not turn an agent review into a claim of independent human approval.
Do not reuse an obsolete head or push directly to main.

## Decisions still needed (record answers in COMMUNICATION.md)

- Exact class paper and submission deadline; final names/roll numbers.
- Moez acknowledgement of shared contracts CO-05/06/08/09/10.
- Actual host/approved access and who supplies raw run evidence if remote access
  is unavailable. No passwords or keys in chat/files.
- Which members perform the real handwriting/review/answer labels. The group
  requirement can be allocated flexibly but cannot be fabricated.
Technical defaults can be chosen from evidence by the implementing agent; do not
ask the user to choose arbitrary thresholds without measurements.

