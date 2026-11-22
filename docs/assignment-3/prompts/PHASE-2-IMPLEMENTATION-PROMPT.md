# Execute Phase 2 - traceability and integration correctness

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


## Entry condition and scope

Verify Phase1 actually landed and its A1/A2/Batch B tests pass. Do not assume a
Phase1 report proves it; inspect ledger/store/metadata and current manifests.
If incomplete, record dependency and complete independent trace tests/interfaces;
do not secretly execute Phase1 scope under a different phase label.

Implement T05/T06, trace portion of T07, coordinate T08 and justified T09 fixes.
Official scope: D1-D4, F4 and integrated B/C/E/F2/F3 correctness; D5 diagnostic tooling
only (the real five-line diagnosis belongs to Phase3 evidence).
Preserve Moez's modules and explicit API seed support. No production tuning/report
claims or real experiment campaign in this phase.

## Ordered implementation

1. Read api/app/{main,schemas,config,logjson}.py, services/{answer,cache,guard,citations}.py,
   retrieval/chroma.py, providers/llm, metrics, API tests and current candidate/eval code.
   Log CO-07..CO-11 coordination and intended shared-file edits before changing them.
2. Introduce a request-scoped trace assembled across actual stages and finalized once.
   Every query outcome must emit one record: answered, declined, cache hit/miss/bypass,
   malformed/provider/retrieval failures where a query is handled.
   Include trace_id=request_id, timestamp, raw and rewritten query, embedding name/
   digest/version, collection and immutable generation, all retrieved chunk IDs with
   doc IDs/versions/scores/text/rank, filters, actual reranked order (or unchanged/no
   reranker), prompt/hash, model/provider/parameters/seed, response/citations,
   guardrail/retry/fallback actions, stage latencies and cache information.
3. Capture exact sanitized context/messages supplied to each model attempt, including
   retry feedback. Preserve original answer provenance on a cache hit; do not invent
   a fresh generation or model call. Do not leak keys, Authorization headers or model
   reasoning that the API contract intentionally strips.
4. Persist JSONL to stdout and configured per-pod trace file on a traces PVC; use safe
   concurrent writes and bounded operational behavior. A file-write failure must not
   crash the answer; expose a diagnostic rather than silently claiming persistence.
   Preserve required traces for refusal/error paths too.
5. Add scripts/trace_tool.py show <trace_id> [paths|-] that reconstructs exact
   context/messages and checks prompt hash using stored evidence, even after reindex.
   Add scripts/trace_summary.py --since --until with top-1 distribution, abstention
   and cache rates, stage p50/p95 and flagged injection counts. Define denominator,
   units/time boundaries, cache bypass and absent-stage semantics.
6. Extend Prometheus metrics for required distributions/per-stage p95; instrument
   question/passages/guard outcomes accurately. Test the valid injected Batch B
   document reaching retrieval and recording actual neutralization/rail actions.
7. Mount trace storage and configure scoped permissions for non-root/read-only-root
   API pods. Keep single-node ReadWriteOnce assumptions explicit. Ensure both API
   and candidate trace wiring/provenance survive integration without opening broad
   network access or granting indexer Redis access.
8. With Moez, make narrow fixes to existing eval/release code:
   - validate golden counts/labels/physical pages before expensive HTTP calls;
   - refuse nonfinite/out-of-range thresholds or results, missing measurements and
     answered-without-citation outcomes; explicit baseline creation/provenance;
   - compare same golden/corpus/config versions for C, keep drift experiments separate;
   - judge exact request-time sanitized evidence rather than rereading possibly newer
     raw chunks; preserve response compatibility or agree additive fields;
   - isolate seed/cache state; avoid global FLUSHALL on a shared Redis instance;
   - resolve coverage.py import collision risk under actual pytest-cov loading;
   - promotion/undo must synchronize live reader, future scheduled ingestion target,
     chunking/model configuration and ledger. A stale gate annotation must not release
     a different candidate; record immutable evaluated provenance;
   - CI must check intended dev2/PR paths, the fourth eval image and separate
     candidate/eval/one-off manifests, not only base Kustomize;
   - keep gate ConfigMap mounted, with no rebuild needed for threshold changes.
   Announce changes to Moez-owned eval/ and release files in the ledger; do not
   duplicate them under new names simply to avoid integration.
9. Validate T08 datasets/provenance. The current draft15-row golden fails 34 checks.
   Help prepare synthetic drafts and page-review tools, but label them truthfully.
   Genuine >=8 hand questions, >=8 human-reviewed synthetic questions and >=8 hand
   answer labels must be supplied by the group. Record who actually supplied them.
   Do not fill those flags from automated inspection.

## Expected files, validation and Definition of Done

Likely additions: API trace service, trace tools, trace unit tests, traces-data PVC,
trace config/mounts. Existing provider/retriever/answer/cache/metrics modules need
instrumentation without discarding guardrails. Small coordinated eval/tests,
release, workflows and manifest fixes are in scope; unrelated backend redesign is not.

Run:
- cd api && python -m pytest tests --cov=app --cov-fail-under=60 -q
- cd indexer && python -m pytest tests -q
- python -m pytest eval/tests -q
- python eval/golden_check.py
- ruff check api indexer eval corpus scripts
- cd api && mypy app
- cd indexer && mypy pipeline
- python -m pip check
- Render and kubeconform -strict production plus separate candidate/eval/job objects.
- Build/scan all four images using pinned existing locks where authorized/available.

All unit tests use fakes and no external model calls. Include trace reconstruction
with source changed/deleted, retry/hit/refusal/error paths, writer failure and
time-window boundaries; gate boundaries/NaN/inf/missing provenance; candidate failure
leaves live unchanged; rollout/undo configuration consistency using a fake kubectl
recorder or approved isolated integration cluster.

Acceptance: complete reconstructable traces/summary/metrics with safe persistence,
required manifests, stable public API, hardening of concrete integration defects,
no claimed human work without evidence, passing actual offline/CI checks or exact
external blockers. Update docs/AI-USAGE.md truthfully and the shared handoff.
No arbitrary measured thresholds, fake trace diagnosis or final screenshots.

## Required end-of-phase report and hard stop

Update COMMUNICATION.md, requirement traceability and assistance/contribution records
with actual actions. Report completed files/features, commands and real outcomes,
regressions, remaining blockers, proposed partner actions, commits/push/PR state and
the precise next phase entry condition. Clearly distinguish IMPLEMENTED from VERIFIED.
Do not publish secrets or full private records in evidence.
STOP at this phase's exit condition. Do not start the next phase automatically.
If a requirement remains blocked, say so; do not declare full assignment completion.

