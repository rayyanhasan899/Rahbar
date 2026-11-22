# Assignment 3 Phase 2 report: traceability and integration correctness

Owner: Rayyan Hassan / rayyanhasan899. Date: 22 November 2026 (PKT).
Scope: T05/T06, trace T07, T08 coordination and justified T09 integration fixes.
Phase3 measurements/submission have not started. Code completion is distinct from
required live evidence, human provenance and genuine partner approval.

## Baseline and authorization

The user explicitly authorized proceeding while Moez is busy and has not reviewed
Phase1. Branch codex/a3-phase-2 starts from Phase1 head8161605; remote dev2 remained
3dff736 after fetch. No pending review was represented as approval and no merge was
performed. Original untracked PROJECT_DOCUMENTATION.md remains untouched/excluded;
SHA256889890d129f5874aa643dc863817634af617ffc7ff3302c9b93c135828eaf8e0.
Moez's original five commits and existing architecture are preserved.

The complete official Assignment_03.pdf was reread (five pages, prior recorded hash),
along with Phase2 prompt, plans, source, gap/handoff/A2 architecture and Phase1 report.
The official D1–D5/F4 requirements control over proposed agent plans. Exact classroom
paper/due date remain HM-01, not invented. Existing Python3.12 environment was
inspected and used unchanged. Initial Phase1 indexer suite54 PASS; Docker engine
pipe unavailable. No host repair, install, secret/account change or new public service.

## Implemented behavior

- One request-scoped terminal trace per handled /api/ask, including malformed/invalid
  input, retrieval failure, refusal, fallback, retries and cache hits. Trace ID equals
  response request_id; provider reasoning/auth headers are excluded.
- Actual Ollama/hosted transport messages, sanitized context, canonical SHA256,
  parameters/seed and retry feedback are captured before each model call. Frozen
  retrieval snapshots prevent embedding/cache and search observing different index
  generations. Pinned embedding artifact mismatch fails before query embedding.
- Additive AskResponse.evidence preserves existing fields and enables judges to use
  exact request-time context. Seed participates in cache identity. Cache hits keep
  original evidence without claiming fresh retrieval/generation; eval bypasses lookup
  and store using X-Rahbar-Cache:bypass. No shared Redis FLUSHALL.
- Stdout plus per-pod persistent JSONL, with locks, budgets and observable write failure.
  API/candidate non-root mounts use traces-data PVC. Existing security/network and
  API-startup read-only behavior remain intact. Single-node RWO assumption explicit.
- trace_tool reconstructs all actual prompts/context and verifies hashes after source
  removal; it reads stored evidence rather than current Chroma. trace_summary uses
  UTC [since,until), nearest-rank p50/p95, observed-stage samples, explicit empty
  rates, error counts, bypass separation and injection/top1 distributions.
- Prometheus top1 and stage histograms, outcomes and trace-write counters extend
  existing metrics. The valid owned BatchB injected document reaches the fake
  retriever and actual mocked provider payload; its recorded neutralization is tested.
  This is offline guardrail proof, not a live ANN retrieval/model demonstration.
- Golden preflight precedes service initialization. Missing/NaN/inf/out-of-range gate
  values, uncited answered responses, missing levels/provenance and noncomparable
  datasets fail closed. API seed must match suite seed. Chunking-only comparisons
  require identical corpus/golden/pairs/embedding/judge/query configuration; drift
  experiments are separate. Independent corpus_sha256 excludes chunk/config caches.
- Baselines require explicit LABEL=baseline/CREATE_BASELINE=true, an absent baseline,
  passing absolute gates and exclusive creation. Candidates cannot become their own
  baseline. Coverage implementation is query_coverage.py; coverage.py preserves CLI
  compatibility while resolving installed coverage for pytest-cov imports.
- Immutable versioned release ConfigMaps and receipts bind evaluated config/template,
  index generation/fingerprint, completed Job UID and result/baseline/decision hashes.
  A stale annotation cannot release changed content. Promotion suspends the scheduled
  writer and refuses active ingestion Jobs; rollout then reconciles writer config/image.
  Undo restores both through release.py undo. Raw kubectl undo requires reconcile
  --resume; failure keeps the writer suspended. The old --force bypass is removed.
- Four image builds/scans and separate manifest validation now run on dev2/feature
  paths. Candidate evaluation uses the source-SHA eval image matching its API;
  make images loads that SHA tag. Root .dockerignore excludes venv/raw corpus/secrets.

Details and limits: docs/adr/0006-traces-and-evaluated-releases.md; k8s/README.md.

## Acceptance traceability

PASS below is scoped to the stated offline/static behavior. Live claims are separate.

| Requirement / criterion | Status | Verification / remaining dependency |
|---|---|---|
| Phase1 dependency intact | PASS offline | Initial54 indexer tests; final55 includes independent corpus fingerprint |
| D1 answered/retry/refusal/error/cache traces | PASS offline | Existing API regressions +11 focused trace tests, including invalid HTTP requests |
| D1 metadata and exact provider attempts | PASS offline | Mocked actual transport payload equality; frozen generation and digest mismatch tests |
| D2 replay after source removal, hash integrity | PASS offline | Replay/hash tamper/cache-origin tests; no live Chroma reads |
| D3 metrics/window aggregation | PASS offline | Half-open window, missing-stage, errors/bypass/empty denominator tests; histograms |
| D4 actual rail action on owned injection | PASS offline | corpus/batch-b/injected-policy.md supplied via fake retrieval; sanitized provider context/asserted action |
| F4 trace PVC/stdout and safe degraded writes | PASS code/static | Writer failure/double-finalization tests; strict schema; live persistence still unverified |
| B exact judged evidence and cache/seed isolation | PASS offline | Suite evidence hash/preflight tests; no current-index judge reads; seed checks |
| C gate/baseline/provenance safety | PASS offline | Numeric boundaries/missing levels/comparability/no-self-baseline tests |
| F3 evaluated release and reader/writer undo | PASS offline | Fake kubectl state validates stale rejection and promote/undo config+image consistency |
| CI four-image/standalone coverage | PASS code/static | All4 builds and all scan executions covered;41 strict objects; full quality/UI blocker separately below |
| T08 valid golden/human provenance | BLOCKED | Current golden checker34 issues; human work/ground-truth pages pending |
| D5 real trace-only five-line diagnosis | NOT VERIFIED | Tooling ready; real PartB failure trace/run must be supplied by Moez |
| Live F2/F3/F4 demo and resource measurement | NOT VERIFIED | Approved Moez host, real Jobs/rollout/persistence/screenshots in Phase3 |
| Genuine partner review/class paper | BLOCKED | Explicit continuation does not supply approval or missing paper |

## Verification commands and actual observations

All tests use fakes/temp files/mock transports, no external models/services.

- `source .venv/rahbar-env.sh` uses existing WSL Python3.12.3.
- `cd indexer && python -m pytest tests -q`:54 initial PASS,55 PASS after corpus
  fingerprint test. Both are actual runs, not saved A2 evidence.
- `ruff check api indexer eval corpus scripts`: PASS at recorded revisions.
- `cd api && mypy app`:26 source files PASS. `cd indexer && mypy pipeline`:17 PASS.
- `cd api && python -m pytest tests --cov=app --cov-fail-under=60 -q`:89 PASS,
 90.92% coverage before last3 trace cases; later focused trace suite11 PASS.
  Final CI counts/coverage supersede this intermediate result below.
- `python -m pytest eval/tests -q`:39 PASS before final missing-level case; final
  suite has40 tests. Focused release/gate16 PASS at its recorded revision.
- `python eval/golden_check.py`: FAIL as expected,34 issues:15 questions,13 answerable,
 2 unanswerable,0 hard; no verified origin/review/physical pages. No flags rewritten.
- `python -m pip check`: No broken requirements found. No local installation.
- `kubectl kustomize k8s/overlays/prod | .venv/tools/kubeconform -strict -summary
 -kubernetes-version 1.34.0`:32 valid,0 invalid/errors/skipped.
- Same strict validator for k8s/jobs/, k8s/candidate/, k8s/eval/, k8s/eval-job.yaml:
 9 valid resources in8 files,0 invalid/errors/skipped.
- `git diff --check`: PASS. Only normal Windows CRLF normalization notices.
- `docker info`: engine unavailable; actual image build/scan evidence comes from CI.

Pre-existing: UI Trivy failure, incomplete golden data, missing real human/paper/host
proof. Introduced and fixed: provider instrumentation type errors; one trace-test
import path; strict ConfigMap settings incorrectly under metadata (CI45029084232).
The corrected manifests subsequently passed the local strict checks above. Existing
release tests were updated to exercise the new immutable receipt contract, not to
allow annotation-only or forced promotion. No unresolved failing test was hidden.

## Changed files

API config/main/schemas, providers/llm/{prompt,ollama,hosted,stub}, retrieval/chroma,
routes/{ask,metrics}, services/{answer,cache,trace(new)} and tests/test_traces(new).
Tools scripts/{trace_tool,trace_summary}(new) and release.py. Eval common/suite/gate/
job, coverage compatibility shim, query_coverage(new), affected coverage/gate/suite/
release tests. Indexer incremental/snapshots plus corpus-provenance test. Kubernetes
API/candidate trace mounts, config, traces-data PVC and kustomization. CI workflow,
root .dockerignore, Makefile, README/runbook, ADR0006, AI record, communication and
this report. No user file deleted; no third-party PDFs/secrets committed.

## Git and integration

Branch codex/a3-phase-2, pushed via Rayyan's existing account. Meaningful code commits:
aeadb93,0b172bc,fd5d034,831f3b9,fed6949. All use Rayyan Hassan's requested identity;
actual assistance is disclosed. Moez's commits remain untouched. Draft PR7
https://github.com/rayyanhasan899/Rahbar/pull/7 is stacked on codex/a3-phase-1 while
PR6 awaits review. Retarget to dev2 after the dependency lands; never pretend the
unmerged Phase1 was reviewed. No main push/merge/force/reset/clean or account changes. Later code milestones2b2e410
(scan completion),ecc6c4a (range checks/evidence),215fd68 (module/noise generation pin)
were also pushed.

## Limits, remaining actions and exact next step

Trace defaults (2MiB record/100MiB per-pod file), first16k passage characters and
initial PVC capacity are operational bounds, not measured thresholds. Disk/fsync
may stall; export/rotation must be managed. Private model reasoning is intentionally
not recorded. Legacy indexes without pinned digest/corpus provenance need a real
verified reindex before authoritative eval. Suite now fails rather than guessing.
Full cluster permission/volume/network/release behavior is not proven by fake tests.

Moez/his agent owns the outstanding host/human handoff: provide exact class paper/due
 date, genuinely author/review required questions and page ground truth, independently
hand-label answers, calibrate actual gate thresholds, fix the existing UI scan, review
PR6/7, run all real Phase3 Jobs/measurements/screenshots and return original result
files/traces. For D5, use a real wrong/refused PartB answer and only its trace; if
Rayyan lacks access, perform that five-line diagnosis and record who actually did it.
Both students still must attend/explain; automation cannot impersonate attendance.

Exact next action: Moez reads COMMUNICATION.md and resolves the human/run-host/review
items; submit PHASE-3-IMPLEMENTATION-PROMPT.md to authorize measured execution when
those entry conditions are available. Phase3 has not started automatically. Do not
call Assignment3 finished or submit Classroom based on this offline phase.

## Intermediate complete CI and final range check

[CI45029781365](https://github.com/rayyanhasan899/Rahbar/actions/runs/45029781365)
at2b2e410 passed lint/types,92 API/55 indexer/40 eval tests,94.29% app coverage,
32 production+9 standalone strict resources and all4 image builds. API/indexer/eval
security scans PASS; UI scan FAIL (pre-existing), quality FAIL, e2e SKIPPED. Scan
matrix fail-fast is disabled solely to finish every scan; no finding is suppressed.
The final metric-range regression adds one eval case.17 focused gate tests PASS.
A fresh-process eval-cwd pytest-cov check ran40 tests successfully, proving the
coverage package collision is resolved (query_coverage58% coverage is not API coverage).

Offline-only trace artifacts are under traces/phase2-offline and the corresponding
summary under eval/results/phase2. They use fake retrieval/Redis and mocked HTTP;
their real local timings must not be used as production/model measurements. Real
cluster trace/release/screenshot/D5 evidence remains assigned to Moez in the ledger.

## Final verified code and phase exit

Final code revision215fd68fb074aeb33cd9a2c4e35e4ff6ddda168e.
[CI45030554656](https://github.com/rayyanhasan899/Rahbar/actions/runs/45030554656)
completed: Ruff/both mypy PASS;92 API+55 indexer+42 eval tests PASS (189 total);
94.29% app coverage;32 production+9 standalone resources strictly valid; all4 image
builds PASS; API/indexer/eval vulnerability scans PASS. UI scan remains FAIL with
6 fixable findings (2 HIGH,4 CRITICAL), quality FAIL and e2e SKIPPED. real-audit was
not requested. Exact run/job URLs/states: eval/results/phase2/ci-summary.json.
No full passing-CI, live model/cluster or release-success claim is made.

Offline reconstruction JSON is committed alongside the clearly labeled fake trace
summary. Actual command `python -X utf8 scripts/trace_tool.py show
97c75d6d8e7d4e21b2c24a48be37a13a traces/phase2-offline` exited0 and verified the
stored prompt without reading Chroma/source files. These are unit-fixture artifacts.
The subsequent final commit contains documentation/evidence only; no rebuilt image
for that documentation SHA is claimed. All code is pushed. Only the original user
PROJECT_DOCUMENTATION.md remains untracked. dev2 still3dff736; main unchanged.

Phase2 code/offline acceptance is met with the explicit external bounds above.
Full-quality/UI, real golden/human provenance, paper/partner review and live D5/F
proof remain open and assigned in COMMUNICATION.md. No required external evidence
is called complete. Phase3 has not begun. The next authorization is the Phase3
prompt after the host/human entry conditions are available.
