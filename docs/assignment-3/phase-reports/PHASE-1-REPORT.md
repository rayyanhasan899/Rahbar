# Assignment 3 Phase 1 report: verified incremental data lifecycle

Owner: Rayyan Hassan / rayyanhasan899. Date: 22 November 2026, Asia/Karachi.
Scope: T01–T04 and ingestion-only T07; official A1/A2, Batch B and ingestion F1/F2.
Implementation and verification are agent-assisted under Rayyan's explicit direction.
Phase 2/3 have not started. This is not an Assignment 3 completion/submission report.

## Outcome and baseline

Verified ingestion, incremental caching/reconciliation, archive/pin/unpin rollback,
safe snapshot publication, owned Batch B, persistent ingestion manifests and focused
tests are implemented. Source changes preserve the API/control-pointer contract and
Moez's evaluation/release algorithms. Offline checks and schema validation pass at
the revisions listed below; live model/cluster demonstrations remain unverified.
The existing UI vulnerability scan fails, so PR #6 remains draft and unmerged.

Authority: the complete five-page `Assignment_03.pdf`, SHA256
`b38d579f4a0d2d6b8b2520f96da4648105ee7d59e8eafd063cf31dac084fda13`;
headings Parts A–G, Tasks Overview, Submission Guidelines and Submission. The relevant
requirements are Part A verification/incremental updates, Batch B planted inputs and
Part F Kubernetes ingestion/persistence. A2's `STARTER.md`, architecture, pipeline,
corpus and existing source contracts carry forward. Partner `docs/a3/*.md` plans are
proposals where they conflict with safe publication or preserved historical queries.
No visible A3 deadline or exact classroom RAGOps paper was supplied locally; HM-01
requests both. A2's November 8 deadline is not reused as A3's deadline.

At start, local `dev` was `3665108`; remote `dev2` was
`3dff73646eaf17ee778a2512f1e1d51166a59ebe` (Moez's five A3 commits), main `e92fbe7`.
Git state, remotes, history and account access were inspected before branching.
Feature branch `codex/a3-phase-1` starts from that `dev2`, preserving all five commits.
Pre-existing untracked `PROJECT_DOCUMENTATION.md` (117576 bytes, November 14 mtime)
was preserved and excluded. Previously prepared local planning files were published
as the first authorized documentation milestone. No remote/main/protection settings,
user data, dependency environment or host configuration were changed.

## Implementation decisions and compatibility

Full contract and rationale: [ADR 0005](../../adr/0005-verified-incremental-publication.md).

- Stable family `doc_id`, numeric version/date, byte SHA256 and opaque family/version
  `doc_key`; original source/section/physical-page/version metadata stays intact.
- Four explicit pass/fail/reason checks per input. Extraction failures continue to
  the next document; failed inputs receive persistent quarantine artifacts. No failed
  near duplicate reaches chunking or chunk embedding.
- Persistent content/config analysis and vectors. Identical reruns reuse extraction
  and both document/chunk embeddings, retaining the generation when storage agrees.
  Invalid updates preserve last verified content. Full configured scopes reconcile
  deletion; omitted scopes are preserved and missing scopes fail safely.
- Archive verified superseded versions, exclude them from default retrieval, support
  rollback pins and unpin without reembedding. Explicit historical-year retrieval
  remains compatible with A2; no golden labels changed. CO-05/06 awaits review.
- Durable immutable ledger revisions precede pointer publication. Staging snapshots
  reuse unchanged vectors, validate exact IDs/metadata/per-document counts and publish
  only when valid. Pointer-selected revisions repair interrupted convenience views.
  Current/archive views are collection-scoped so candidate indexing cannot overwrite
  live materialized files. Existing shared flock covers all writer entry points.
- “Changed-only” refers to extraction/embedding work and changed document content.
  Unchanged vectors are physically copied into each new immutable snapshot. Retired
  collections remain intentional recovery/in-flight history, not asserted absent.
- Same embedding model, actual Ollama digest, dimension and configuration fingerprint
  are required. A conflicting model/digest/chunk config needs a separate collection.
  No indexer-to-Redis permission or API-startup indexing was added.

CO-05 interprets successful recency as orderability plus active-version selection;
older verified input is archived with a reason naming the active version. Actual
recency/other check failures quarantine. This explicitly resolves A1's failed-input
wording against A2 archive/history requirements. It differs from the partner plan's
recency-fail exception/delete-first design; no partner acceptance is invented.

## Requirement and acceptance traceability

PASS here means the stated implementation/offline criterion was observed. It does
not turn a schema/fake test into a live Kubernetes observation. AC19 tracks that
separately. Shared human review and the full security gate remain open.

| ID / requirement | Evidence and verification | Status | Remaining work |
|---|---|---|---|
| AC01 T01 baseline/preservation | Git inspection; feature from dev2; original partner commits and untracked document preserved | PASS | Genuine PR review |
| AC02 T01 additive identity/pointer contract | models.py, incremental.py, snapshots.py; ADR0005; existing API81/eval33 tests | PASS | CO-05/06 review; query digest/trace integration Phase2 |
| AC03 A1 four checks | verify.py; extraction/metadata/page/truncation/garbling/version/finite-vector tests; all owned batch inputs get four reasons | PASS offline | Inspect real PDFs/OCR outcomes on run host |
| AC04 A1 quarantine before chunking | incremental.py; corrupt/missing/duplicate tests, chunking spy rejects accidental near-duplicate chunking | PASS offline | Actual quarantine screenshot later |
| AC05 A2 unchanged zero embeddings | test_unchanged_run_skips_all_embedding_and_extraction; rejected-near-duplicate cache test; stable generation assertions | PASS offline | Confirm zero calls with real model |
| AC06 A2 changed-only work | changed document test checks other IDs/vectors preserved; failed updates keep prior verified content | PASS offline | Real changed-file Job measurement |
| AC07 A2 deletion/no current orphans | deletion, partial/missing-scope, equal-count wrong-ID and repair tests; pipeline.counts | PASS offline | Live per-doc count/ID evidence |
| AC08 A2 archive/restore/unpin | newer/older versions, declared superseded and renamed replacement tests; rollback test checks no embeddings | PASS offline | Live default/history/rollback demo |
| AC09 A2 interrupted publication | pre-pointer failure and post-pointer materialization failure tests; authoritative revision recovery | PASS offline | Live interrupted Job evidence |
| AC10 A2 config/candidate isolation | model/digest/chunk mismatch tests; legacy-model rejection; candidate-view isolation | PASS offline | Query digest validation in Phase2 |
| AC11 ingestion F2 serialized writers | existing Linux cross-process flock test; all entry-point wrappers and shared /locks mounts inspected | PASS offline | Concurrent manual/scheduled Jobs Phase3 |
| AC12 Batch B >=10 owned inputs | generator, manifests and EXPECTED.md; 13 BatchB docs + BatchA control; hashes/reproducibility tested | PASS | Real near cosine measurement, not fake value |
| AC13 T04 compatible transfer | test_corpus_transfer: zero-argument deploy caller, destination/tar/hash/path validation; no cluster calls in tests | PASS offline | Actual transfer/persistence proof |
| AC14 F1/F2 manifest wiring | datalake PVC; Job/Cron mounts; standalone verify/rollback/inspection; production31 + standalone3 strict schemas valid | PASS static | PVC persistence/permissions on run host |
| AC15 verification/count/rollback commands | run --verify-only; counts actual IDs/meta; rollback CLI; wrapper lock/config inspected and lifecycle tests | PASS offline | Real CLI/Job invocation evidence |
| AC16 lint/types/tests/build | Local/CI command results below; no failing new-code checks remain in the verified revisions | PASS at recorded revisions | Final head confirmation recorded below |
| AC17 docs/handoff/traceability | this report, ADR0005, architecture/corpus/pipeline/runbooks, communication ledger and AI disclosure | PASS | Moez reply and subsequent-phase updates |
| AC18 shared interpretation/PR approval | CO-05/06/09 and HM-03/09 pending; PR6 is draft | BLOCKED | Moez must review actual diff and decisions |
| AC19 real Part A / Kubernetes proof | no new live model/cluster run in this phase; Docker daemon unavailable | NOT VERIFIED | Phase3 run host, raw reports/logs/screenshots and measurements |
| AC20 full CI/security | unchanged UI scan reports6 fixable findings; e2e skipped; other scans can be canceled by fail-fast | FAIL pre-existing | HM-10 separate UI fix, scans and e2e rerun |

Acceptance register: 17 PASS (with the stated offline/static bounds), 1 BLOCKED,
1 NOT VERIFIED, 1 pre-existing FAIL. This is a Phase 1 register, not a percentage
completion estimate for all Assignment 3 requirements.

## Files created, modified and preserved

| Area | Files |
|---|---|
| New pipeline modules | indexer/pipeline/datalake.py, verify.py, incremental.py, snapshots.py, rollback.py, counts.py |
| Existing pipeline integration | indexer/pipeline/run.py, config.py, models.py, extract.py, embed.py |
| New focused tests | indexer/tests/test_incremental.py, test_verification.py, test_corpus_transfer.py |
| Owned fixture generation | corpus/generate_batch_b.py; corpus/batch-a/_index.json and control-policy.md; corpus/batch-b/_index.json, EXPECTED.md and13 planted files |
| Corpus metadata/transfer | corpus/sources.yaml, corpus/fetch.py, scripts/corpus_transfer.py |
| Additive eval metadata only | eval/fixtures/academic-rules-2023.md, academic-rules-2026.md, fees-2026.md |
| Ingestion Kubernetes | k8s/base/datalake-data.yaml, kustomization.yaml, indexer-job.yaml, reindex-cronjob.yaml, configmap.yaml; k8s/jobs/verify-only-job.yaml, rollback-job.yaml, datalake-inspect.yaml |
| CI | .github/workflows/ci.yml: additional strict standalone-ingestion-object validation only |
| Current documentation | ARCHITECTURE.md, README.md, k8s/README.md, docs/CORPUS.md, PIPELINE.md, REQUIREMENTS.md, AI-USAGE.md; docs/adr/0005-verified-incremental-publication.md; assignment-3 status/handoff and this report |
| Published planning baseline | docs/assignment-3/{README,ASSIGNMENT-3-GAP-ANALYSIS,ASSIGNMENT-3-THREE-PHASE-PLAN,COMMUNICATION}.md and three prompts |
| Offline evidence | eval/results/phase1/offline-checks.json with native test names, results and source hashes; CI links below |

No project files were deleted. No third-party downloads, credentials or private
student data were committed. Batch B's two tiny malformed PDFs are owned generated
test bytes. Existing `eval/*.py`, golden labels, `scripts/release.py`, API behavior
and partner candidate/eval manifests were preserved. No new dependency was added.

## Commands and actual verification

All commands run from repository root unless a directory change is shown. No test
calls an external service/model. Actual image builds/schema checks ran on GitHub's
existing runner; no dependency installation or cluster repair was performed locally.

| Command / evidence | Actual result |
|---|---|
| `wsl -d Ubuntu -- bash -lc 'source .venv/rahbar-env.sh && cd indexer && python -m pytest tests -q'` | Initially WSL startup E_UNEXPECTED; later existing environment recovered without repair and all53 indexer tests PASS |
| Native Python3.14.7 `-B -m unittest discover -s indexer/tests -p test_incremental.py -q` |24 PASS after final collection-view test |
| Same native command with test_verification.py / test_corpus_transfer.py |7 /3 PASS |
| Native `python -B .venv/phase1_evidence.py` |34 PASS; committed offline-checks.json records exact test IDs/source hashes; helper is ignored local scratch |
| `kubectl kustomize k8s/overlays/prod` (installed Windows kubectl), YAML parse |31 resources, exactly one base Job named indexer; separate Jobs do not change deploy_local's first-Job selection |
| CI `ruff check api indexer eval corpus scripts`; mypy app / pipeline |PASS in45012154398 and45012559308 |
| CI `cd api && pytest -q --cov=app --cov-report=term-missing --cov-fail-under=60` |81 PASS;93.31% app coverage in both above runs |
| CI `cd indexer && pytest -q`; `pytest -q eval/tests` |48/33 PASS at1fd8a65;52/33 PASS at6e0edba; final view-isolation test adds one indexer test |
| CI production strict kubeconform, Kubernetes1.34.0 |31 valid,0 invalid/errors/skipped |
| CI strict kubeconform k8s/jobs/ |3 valid,0 invalid/errors/skipped |
| CI docker build api/indexer/ui, SHA-tagged local runner images |All3 PASS at1fd8a65 and6e0edba; no publishing/CD claim |
| `git diff --check` |PASS; only normal Windows CRLF normalization notices |
| `docker info --format '{{.ServerVersion}}'` |FAIL: DockerDesktopLinuxEngine pipe unavailable; no daemon start/repair attempted |

Runs: [baseline45010313761](https://github.com/rayyanhasan899/Rahbar/actions/runs/45010313761),
[45012154398 at1fd8a65](https://github.com/rayyanhasan899/Rahbar/actions/runs/45012154398),
[45012559308 at6e0edba](https://github.com/rayyanhasan899/Rahbar/actions/runs/45012559308).
Manual workflow dispatch uses the feature branch and `real_audit=false`; existing
push/PR triggers do not cover this branch/base combination automatically. No CI
test, quality gate or security scan was disabled to manufacture a pass.

### Failures and limitations

Introduced and corrected during this phase: untyped YAML import/type inference in
the new ledger path (CI45011465659), and the standalone inspection Pod incorrectly
using batch/v1 (CI45011791121). Later lint and strict schema runs passed. Review also
fixed chunking before near-duplicate rejection and collection-view collisions,
with focused regression tests. No unresolved introduced test failure is hidden.

Pre-existing: baseline45010313761 already failed the unchanged UI vulnerability gate.
At45012154398 Trivy reported nginx1.30.6-r1, fixed1.30.7-r0, with four CRITICAL
(CVE-2026-113425,121810,123007,123633) and two HIGH (CVE-2026-118899,123634).
These are the scanner's actual observations, not an independently established
exposure analysis. HM-10 asks Moez to fix/rebuild separately. API/indexer scan
cancellation is not a pass, and skipped e2e is not a successful fixture deployment.

Known bounds: heuristic quality/truncation and numeric version ordering; bounded
first4000-character document embedding can miss later duplication; provisional .995
near threshold; one document's extraction/cache is held in memory. Embedding batches
default16; Chroma page/add batches128. Snapshot/blob/quarantine retention consumes
storage (initial data-lake1Gi claim needs real measurement); no automatic GC was
added. Query-time model-digest validation/traces remain Phase2. Current-generation
orphan checks do not assert that retired snapshots have been deleted globally.

## Git, contribution and review state

Meaningful milestones pushed through Rayyan's authenticated account:
490ca5f (shared scope/handoff), c978f0f (verified incremental pipeline), 9b4544d
(rejected-analysis cache/types), 1fd8a65 (snapshot identities/archive semantics),
6e0edba (transfer/snapshot tests and pre-chunk duplicate rejection).
Final documentation/isolation milestone and check results are appended below.
Commit authorship is Rayyan's requested identity; actual code/test operator is Codex
under his instruction, disclosed in AI-USAGE.md. Moez's existing contribution and
original commit identities are preserved. No partner review was fabricated.

Draft [PR #6](https://github.com/rayyanhasan899/Rahbar/pull/6) targets `dev2`, not main.
It is unmerged and the full quality gate is not green. No force-push, history rewrite,
reset/clean/stash, remote change, main push or account-setting change was performed.

## Remaining work, owners and exact next action

Moez/his agent: read COMMUNICATION.md, review CO-05/06 (recency/history) and CO-09
(future candidate promotion/writer target), review PR6 and acknowledge actual changes.
Address HM-10 UI scan in a separate scoped change. Supply the exact class paper and
A3 due date (HM-01); confirm approved run-host access (HM-02). The shared file is
published but does not automatically notify a second agent.

Human group members: actually write/review required questions and hand labels;
provide names/roll numbers, review contributions, understand/explain all parts and
perform genuine partner approval. No AI output is represented as that human work.

Phase3/run host: execute the documented dependency-first transfer/Job workflow,
measure real near-duplicate scores, real corpus acceptance/recency, unchanged0-call
rerun, changed/deleted counts, archive/rollback, interruption/serialization and PVC
persistence. Save original reports/logs and actual screenshots; do not substitute
these offline results for them. Existing historical A2 scores are not A3 reruns.

Exact next action: have Moez review the published Phase1 contracts/diff and resolve
the scoped handoff; when authorizing further implementation, submit
`docs/assignment-3/prompts/PHASE-2-IMPLEMENTATION-PROMPT.md`.
That phase must re-inspect the branch/current host state and preserve this work.
This session stops at Phase1; no tracing/evaluation redesign or Phase3 demo began.
