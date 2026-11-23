# Execute Phase 1 - verified incremental data lifecycle

## Standalone context and mandatory first steps

Repository: D:/RAYYAN/ASSIGNMENTS/Software Construction and Development/Assignment2/rahbar-starter
GitHub: https://github.com/rayyanhasan899/Rahbar
Owner: Rayyan Hassan / rayyanhasan899; requested author email rayyanhassan899@gmail.com.
Partner: Moez / AbdulMoez-24i-3048-SE-B.
Assignment: CS4032 Fall26 Assignment03, 185 marks, two people, continuation of A2 RAHBAR.
Official source: D:/RAYYAN/ASSIGNMENTS/Software Construction and Development/Assignment_03.pdf
Five pages; SHA256 at planning was b38d579f4a0d2d6b8b2520f96da4648105ee7d59e8eafd063cf31dac084fda13.
Re-read all five pages, the exact class RAGOps paper when supplied, applicable AGENTS.md,
STARTER.md, current source/tests, docs/assignment-3/{README,ASSIGNMENT-3-GAP-ANALYSIS,
ASSIGNMENT-3-THREE-PHASE-PLAN,COMMUNICATION}.md, and partner docs/a3/*.md before editing.
If the official PDF is inaccessible, locate the identical supplied document or ask
for it; do not replace its requirements with generic RAGOps assumptions.

The inspected A3 branch was dev2 at 3dff73646eaf17ee778a2512f1e1d51166a59ebe.
Local dev at planning was 3665108, with untracked PROJECT_DOCUMENTATION.md.
These are dated observations, not permission to discard newer work. Recheck cwd,
full relevant tree, instructions, git status (tracked/untracked), branches, remotes,
recent commits and live remote synchronization first. Inspect credential-free remote
URLs and gh account access. Do not ask for passwords/tokens when already authenticated.

Moez implemented B/C/E and evaluation/release F scaffolding in eval/*.py,
scripts/release.py, k8s/eval-job.yaml, k8s/eval/ and k8s/candidate/. His plan allocates
Rayyan A/D and data-lake/trace F. Reuse current implementations. The existing system
is Python3.12 FastAPI/Pydantic, Chroma client/server1.0.12, Redis, Ollama embeddings/
generation, plain browser UI, Kustomize and GitHub Actions. No new framework/database
or hosted platform is necessary.

## Safety, identity and coordination

This prompt authorizes ONLY the phase named below, not the other two.
Use Rayyan's verified Git identity/account for authorized milestones; do not replace
partner authorship or introduce an assistant as the Git author. Actual assistance
must remain honestly disclosed. Do not claim automated writing/review as independent
handwriting, invent data, personal debugging time, approvals, screenshots or run results.

Read and update COMMUNICATION.md at session start/end and before overlapping edits.
Publish that ledger with the first authorized docs milestone if it is still local,
so Moez can read/respond. This file does not automatically message anyone.
Preserve Moez's code, especially eval/ and release orchestration. Log proposed
cross-owner edits and interface changes before implementing them. Continue independent
additive work through coordination or host blockers. Record inaccessible work with
exact commands, owner and required evidence; never mark it complete.

Preserve user changes and untracked files. Prefer an isolated codex/a3-phase-N feature
branch/worktree from current reviewed dev2, PR back to dev2. Fetch/pull normally only
after inspecting state. Never git-init, reset/clean, force-push, rewrite authors,
replace the remote, push directly to main, bypass protection or auto-supply human review.
Commit meaningful tested milestones and push through Rayyan's account when ready,
without needless microcommits. Obtain genuine required partner review for protected
merges; do not claim a forged or agent-only review was an independent human approval.

Inspect existing .venv/rahbar-env.sh and Python3.12 environment before using/changing it.
Do not install tools, change host RAM/firewall/accounts, expose new services or repair
the previously rejected Docker socket without relevant authorization. Credentials
belong in secure account/Secret facilities, never source/logs/communication files.
Moez's16GB laptop is the planned run host; that plan is not proof of access/readiness.
Rayyan's8GB host previously failed model allocation. Recheck before real runs.

Keep API startup read-only, one locked ingestion writer, compatible model/dimension
pin, active pointer and old verified data until replacement succeeds. Keep security,
truthful probes, bounded workloads and existing valid response fields. Preserve
prompt-injection controls, schema/citation validation, fallback and cache protections.

No optional UI rewrite, auth, cloud migration or novel reranker. Use fakes/mocked
services for offline tests. A similarly named file or an old report is not verification.
Record exact commands/results, blockers and evidence; never weaken a test/checker/gate
to get green.


## Objective, exact scope and dependencies

Implement tasks T01-T04 and the ingestion portion of T07 from the three-phase plan.
Official scope: A1 verification, A2 incremental update/archive/rollback, Batch B,
and ingestion-related F1/F2. Specify additive D metadata contracts only; do not
implement query tracing or rewrite Moez's evaluation/release modules in this phase.

Start with docs/a3/AI-TASKS-RAYYAN.md, pipeline/{run,extract,clean,chunk,embed,store,
models,config}.py, corpus/fetch.py and metadata, scripts/{corpus_transfer,deploy_local,
render_stack}.py, k8s/base indexer/CronJob/config/PVC resources and existing tests.
Log CO-01..CO-06 decisions with Moez. The official PDF wins over proposed plans.

## Ordered implementation

1. Define stable document family doc_id, version/immutable content hash/doc_key,
   physical page/section/source metadata and configuration fingerprint. Retain
   <collection>-control / active / active_collection, model/dimension and generation
   fields required by API/eval. Separate ledger per collection/config.
2. Add verification after ingestion/extraction and before chunking: quality,
   completeness (source/title/date-or-version/page count/truncation), recency and
   uniqueness (exact hashes and document-embedding similarity). Each document needs
   four explicit pass/fail/reason results even when extraction fails.
3. Route failed incoming inputs to persistent quarantine with machine-readable reasons
   and one run report. Do not index their chunks. Reconcile A1's quarantine wording
   with A2 archival of previously accepted superseded versions. Do not silently
   implement the plan's alternative treatment of recency failures.
4. Add persistent current/archive/quarantine/reports/state ledger and incremental
   reconciliation. Cache extraction and document embeddings by bytes/config, so the
   unchanged rerun makes ZERO embedding calls as well as zero chunk embeddings.
   Changed document updates its own chunks; absent documents reconcile by doc identity
   across every configured input folder; do not misinterpret a partial batch as deletion
   of all previously accepted documents. Count active/archived chunks per document,
   verify ledger/vector agreement and prove no orphans.
5. Retain safe publication. Never remove a working document before replacement vectors
   validate; test interrupted runs, malformed updates and pointer/ledger reconciliation.
   Archive accepted superseded versions, exclude from live retrieval through metadata,
   and restore/unpin through an ingestion-side rollback/count command. Preserve explicit
   historical semantics unless a reviewed contract change is recorded.
6. Keep shared writer lock across manual/scheduled/rollback Jobs. Refuse reuse when
   embedding model/dimension/digest or chunking fingerprint conflicts; use a separate
   candidate collection. Unchanged retrieval state must not advance generation.
7. Generate >=10 owned Batch B documents reproducibly, with hashes and EXPECTED.md:
   >=2 exact duplicates, one near duplicate, truncated/corrupt input, missing metadata,
   newer version and an injected instruction. Additional clean/garbled fixtures help.
   Preserve a valid injection document for later retrieval-rail proof. Do not claim
   injection defence merely because the document was never indexed.
8. Extend corpus transfer without breaking deploy_local.py. Add data-lake PVC/mounts
   to ingestion Job/CronJob, scoped writable directories and config. Keep one-off
   verify/rollback Jobs outside base if deploy_local selects its first Job.
9. Send HM-01..HM-05 host/paper/human-data requests through the communication ledger
   early; no invented replies or human labels.

## Expected files and exclusions

Likely additions: indexer/pipeline/{verify,ledger,datalake,rollback,counts}.py
(or smaller equivalent modules justified by code), corpus/batch-b fixtures/generator,
indexer/tests/test_verification.py and test_incremental.py, data-lake PVC and scoped
one-off Job manifests under k8s/, docs explaining lifecycle/recovery.
Modify existing runner/store/models/config/extraction/transfer and manifest wiring
only as necessary. Coordinate required fixture front-matter additions with Moez.
Do not replace eval suite, change existing golden labels to hide failures, perform
real benchmark tuning or write final report numbers. No cluster deletion.

## Tests and acceptance

Use fake embedder/store/clock/filesystem fixtures and isolated temporary corpora.
Tests must cover all four checks, corrupt input continued processing, exact/near
duplicates, newer/older versions, unchanged zero calls, changed-only update,
deleted-document reconciliation, invalid-update preservation, archive/restore,
collection/config isolation, path traversal, lock serialization and crash recovery.
Assertions should verify behavior and storage invariants, not mirror code structure.

Run appropriate commands from the inspected environment:
- cd indexer && python -m pytest tests -q
- ruff check indexer corpus scripts
- cd indexer && mypy pipeline
- Existing transfer/contract tests affected by edits, and eval tests after coordination.
- kubectl kustomize k8s/overlays/prod; existing kubeconform with -strict and tested
  Kubernetes version, plus separate new Job manifests.
Do not execute live ingestion merely to check the runner. If WSL still fails,
diagnose without unauthorized host repair; use existing approved CI/partner runner
and record missing results honestly.

Definition of Done: A1/A2/Batch B code and fake tests exist and pass; metadata/pointer
contract and safe recovery are documented; ingestion manifests render/validate;
meaningful Rayyan-authored milestones/PR preserve Moez's work. Runtime demonstrations
remain explicitly assigned to Phase3. No full A3 completion claim.

## Required end-of-phase report and hard stop

Update COMMUNICATION.md, requirement traceability and assistance/contribution records
with actual actions. Report completed files/features, commands and real outcomes,
regressions, remaining blockers, proposed partner actions, commits/push/PR state and
the precise next phase entry condition. Clearly distinguish IMPLEMENTED from VERIFIED.
Do not publish secrets or full private records in evidence.
STOP at this phase's exit condition. Do not start the next phase automatically.
If a requirement remains blocked, say so; do not declare full assignment completion.

