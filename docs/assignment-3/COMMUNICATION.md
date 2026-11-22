# Assignment 3 shared communication and handoff

Project owner for this work: Rayyan Hassan / rayyanhasan899.
Partner: Moez / AbdulMoez-24i-3048-SE-B.
Created: 22 November 2026, Asia/Karachi. Status: PHASE 2 CODE/OFFLINE VERIFIED; REVIEW/HUMAN/RUNTIME EVIDENCE PENDING.

This is the shared ledger for Rayyan's automation and Moez/his agent. Read it at
the start and update it at the end of every implementation session. It is a file,
not a running channel: no other agent is notified merely because it changes.
At creation it is LOCAL ONLY because this planning task forbids Git-state changes.
The first authorized implementation session should publish the documentation through
a feature branch/PR targeting dev2, so Moez can read/reply. No account access is missing
for Rayyan's existing repository: gh is authenticated and push/admin access was checked.

## How to communicate

Append entries; do not erase another member's entries. Label each entry with date,
owner/account, assistance/operator where known, branch/commit, requirements, files,
actual commands/results, blockers, next step and links to evidence.
Use PROPOSED, IN PROGRESS, IMPLEMENTED, VERIFIED or BLOCKED precisely.
A checkbox is not evidence. A planned run is not a successful run.
Never put credentials, tokens, private keys or private student data here.
When simultaneous edits conflict, preserve both entries and resolve normally;
never reset, force-push or overwrite another person's section.
Do not attribute an entry or approval to Moez unless he actually supplied it.

## Planning baseline (historical, before Phase 1)

- Local dev: 3665108; untracked PROJECT_DOCUMENTATION.md must be preserved.
- GitHub main: e92fbe7; GitHub dev2: 3dff736 (five A3 commits ahead).
- Moez's implemented scaffolds: B suite/golden tooling, C gate, E coverage,
  F evaluation objects/candidate release, provider SEED support.
- Rayyan's A/D and ingestion/trace F implementation: NOT STARTED in inspected dev2.
- A3 results, traces, human review records and report PDF: not supplied/verified.
- Full unit testing is blocked on Rayyan's current WSL startup error E_UNEXPECTED;
  do not replace the environment or call saved A2 test output a new pass.
- These new planning documents do not change application code or represent a phase run.

Current Phase 1 implementation/acceptance evidence is in
[PHASE-1-REPORT.md](phase-reports/PHASE-1-REPORT.md) and the appended session log.
The historical baseline above is not the current implementation status.

## Interface decisions to resolve before affected integration

| ID | Proposal / concern | Lead | State |
|---|---|---|---|
| CO-01 | Stable family doc_id; separate immutable version/hash/doc_key; retain source/section/page/doc_version/superseded | Rayyan + Moez | PROPOSED |
| CO-02 | Keep <collection>-control / active / active_collection and generation contract; generation changes only when retrievable content/config changes | Rayyan | PROPOSED |
| CO-03 | Unchanged corpus makes zero document/chunk embedding calls via persistent hash/config cache; bad changes preserve last verified content | Rayyan | PROPOSED |
| CO-04 | Do not delete live chunks before replacement is safely prepared; define crash/recovery and publication ordering with tests | Rayyan | PROPOSED |
| CO-05 | A1 failed incoming documents quarantine; previously accepted superseded versions archive. Explicitly reconcile recency outcomes with official A1 wording | Both | OPEN |
| CO-06 | Preserve explicit historical queries unless a reviewed decision says otherwise; do not silently change q10 or old golden labels | Both | OPEN |
| CO-07 | Trace uses request_id, immutable generation, exact sanitized model context/messages, model digest, filters, rail actions and stage timings; cache hits link original provenance | Rayyan | PROPOSED |
| CO-08 | Evaluation judge reads request-time evidence, not a possibly newer/raw collection; additional API/trace interface must be agreed before changing eval | Both | OPEN |
| CO-09 | Promotion and undo must keep future ingestion target/chunking/ledger consistent with API collection, not just set API env | Moez + Rayyan | OPEN |
| CO-10 | Candidate baseline/golden/corpus/model provenance must match; candidate cannot auto-create its own baseline | Moez | OPEN |
| CO-11 | New eval image/tests and standalone manifests need CI coverage on dev2/PRs; finite gate thresholds and valid golden before model calls | Moez, Rayyan can implement scoped fixes after logging coordination | OPEN |
| CO-12 | No reranker is mandatory: log actual retrieval order and explicitly identify reranking as not applied | Rayyan | PROPOSED |

No response is fabricated. Work independently on additive A/D modules and fake tests
while awaiting a reply; do not silently impose a breaking contract on Moez's code.

## Requests for Moez / his agent

| ID | Exact action needed | Why / evidence required | State |
|---|---|---|---|
| HM-01 | Supply official due date and exact class RAGOps paper/version | Not visible in assignment PDF / no exact class copy | PENDING |
| HM-02 | Confirm 16 GB host is available and provide approved execution/access method, or run supplied commands and return original result files/logs | Rayyan's host was memory-constrained; no remote access currently established | PENDING |
| HM-03 | Review CO-01 through CO-11, especially quarantine/history, judge evidence and reader/writer promotion consistency | Avoid incompatible parallel edits | PENDING |
| HM-04 | Human group members write >=8 original questions with document/page ground truth | An agent can draft synthetic questions but cannot claim handwritten origin | PENDING |
| HM-05 | Human group members review >=8 synthetic questions against pages and independently label >=8 answers before seeing judge outputs | AI-only checks cannot be recorded as hand review/hand labels | PENDING |
| HM-06 | Participate in real Batch A/B, unseen ingestion, eval Job, gate fail/pass/ConfigMap edit, release/undo and trace demonstrations | Own cluster and uncropped terminal screenshots required | PENDING |
| HM-07 | Capture raw A-F screenshots, results and resource measurements if Rayyan's automation has no approved GUI/cluster access | Screenshots must show actual command/output, not recreated terminal text | PENDING |
| HM-08 | Supply both final names/roll numbers, review contribution/AI statements and attend/explain all parts | Agent cannot attend as either student or invent knowledge/approval | PENDING |
| HM-09 | Review passing implementation PRs; merge only through existing protection | Existing approval rules remain enabled; no invented review | PENDING |

The assignment requires human work by the GROUP, not necessarily an equal four/four
split. Moez may perform the genuine manual requirements if he actually does them;
record the true allocation. Rayyan's automation can build, debug, run accessible
experiments, analyze results, prepare the report and organize submissions. It cannot
convert its own questions into human-origin questions or impersonate a student.

## Ownership and overlap

Rayyan's implementation: indexer/pipeline, corpus Batch B tooling, trace services/tools,
data-lake/trace PVCs and ingestion-side Jobs.
Moez's implementation: eval modules, gate/coverage, scripts/release.py, candidate/eval
Kubernetes resources. They are not finished just because code exists.
Shared hotspots: api/app/config.py, schemas.py, services/answer.py, retrieval/chroma.py,
providers, k8s/base/api.yaml/configmap.yaml/networkpolicy.yaml, Makefile, README,
k8s/README.md, .github/workflows/ci.yml. Announce intended edits here before changing
shared or Moez-owned files. Coordinate eval fixture metadata additions.

## Session log

### 22 November 2026 - Rayyan - planning and access check
Status: PLAN PREPARED.
Assistance: automated repository inspection and planning under Rayyan's direction.
Account: rayyanhasan899; Git identity Rayyan Hassan / rayyanhassan899@gmail.com.
Official PDF reread in full; hash recorded in README.
Live dev2 and all five commit author records rechecked; no app work copied/rewritten.
Created the gap analysis, plan, three future prompts and this ledger.
No application edits, dependency installation, branch changes, commits, pushes,
account changes, paid calls or cluster changes made.
Next: Rayyan submits the Phase 1 prompt; publish the ledger in that authorized phase,
then implement additive verification/incremental lifecycle with fake tests.

### Reply template
Date:
Owner/account:
Assistance/operator:
Branch and commit:
Requirements and files:
Actual command and result:
Decision/request IDs answered:
Blockers and evidence:
Next action / owner:

### 22 November 2026 - Rayyan - Phase 1 started
Status: IN PROGRESS. Branch: codex/a3-phase-1, based on dev2 3dff736.
Scope: A1/A2, owned Batch B and ingestion-side F1/F2 only. Existing untracked
PROJECT_DOCUMENTATION.md is preserved and excluded from commits.
Baseline: WSL still fails before pytest with E_UNEXPECTED; Docker daemon is stopped.
No host repair or cluster startup has been attempted. Linux verification will use
the existing GitHub runner while independent implementation continues.
Proposed safety resolution CO-02/04: immutable published snapshots reuse unchanged
chunk vectors; prepare durable ledger revision before switching the active pointer.
No delete-before-embed. Old snapshots remain explicit recovery/in-flight history,
not current searchable orphan chunks. Counts will identify collection/generation.
CO-05: failed incoming inputs quarantine; prior accepted versions archive on
supersession. CO-06: preserve explicit historical requests and golden labels pending
joint review; default queries still exclude superseded/archived content.
Shared edits planned: additive metadata/config, corpus fetch/transfer and ingestion
manifests. eval algorithm/release code will not be rewritten. Fixture front matter
may need additive title/doc_id/pages for verification; announce it before editing.
Requests HM-01..HM-05 remain pending; no partner reply or human work is assumed.

### 22 November 2026 - Rayyan - additive compatibility decisions
CO-05 interpretation implemented for review: recency checks PASS when ordering and
newer-version detection succeed, recording the selected active version. A successfully
verified older version is ARCHIVED, not a failed input. Actual verification failures
quarantine and never index. This satisfies four explicit check results without
silently indexing a failed document or removing A2's explicit historical retrieval.
CO-06: no golden question changed; default metadata marks archived=true and
superseded=true, preserving current API filtering and explicit historical requests.
No claim of Moez approval. His plan's fixed long-lived collection/delete-first
algorithm is deliberately not adopted; safety rationale is in the lifecycle ADR.
Shared edit notice: adding doc_id/title/pages to the three owned eval fixtures only,
without changing their policy text, labels or any evaluation algorithm. Also adding
family IDs to corpus sources/fetch metadata and --source/--dest transfer options.
Baseline CI45010313761: lint/tests/manifests and three builds passed; unchanged UI
image failed the vulnerability gate. e2e was skipped. The scan is not disabled;
Moez's security/build follow-up remains separate from Phase1 ingestion correctness.


### 22 November 2026 - Rayyan - Phase 1 verification update
Status: IMPLEMENTED, offline checks passing; live Kubernetes NOT VERIFIED.
Published branch codex/a3-phase-1 and draft PR #6 target dev2:
https://github.com/rayyanhasan899/Rahbar/pull/6
Milestones: 490ca5f, c978f0f, 9b4544d, 1fd8a65. All use Rayyan's requested identity;
actual implementation/test execution is agent-assisted under Rayyan's direction.
Shared CI change notice CO-11: added only strict validation of k8s/jobs/ to the
existing manifests job. No evaluation/release algorithm, gate or labels changed.
CI45012154398: Ruff, both mypy checks, API81/indexer48/eval33 tests and 93.31% API
coverage PASS; production31 and standalone3 strict resources PASS; three builds PASS.
Earlier introduced type errors and the inspection Pod's apiVersion were fixed and
reverified. New transfer/snapshot adapter tests also pass locally. Uniqueness now
finishes before chunking; failed near duplicates cannot reach chunking.
UI scan remains FAIL on the unchanged nginx image: installed1.30.6-r1, fixed1.30.7-r0;
CVE-2026-113425, CVE-2026-121810, CVE-2026-123007, CVE-2026-123633 (CRITICAL),
CVE-2026-118899 and CVE-2026-123634 (HIGH), as reported by Trivy in that run.
HM-10 (Moez, PENDING): separately update/rebuild the pinned UI image, rerun all scans
and the blocked e2e suite. Do not suppress findings. Other scan matrix jobs may be
cancelled by fail-fast; their cancellation is not a scan PASS.
HM-01..HM-09 and CO-05/06/09 approvals remain pending; no reply is assumed.

### 22 November 2026 - Rayyan - Phase 1 final verification and handoff
Status: IMPLEMENTED; final checks running; Phase2/3 NOT STARTED.
Collection-scoped current/archive views now prevent candidate overwrites; regression
covered. ADR0005 and runbooks document safe publication, retention costs, recency/history
interpretation, provisional threshold and actual remaining runtime proof.
Local Windows offline evidence: eval/results/phase1/offline-checks.json, 34 PASS,
Python3.14.7, fake vectors/store/cluster calls (not model or Kubernetes evidence).
WSL subsequently recovered without host repair. Existing Python3.12 indexer suite
now53 PASS; remaining local Ruff/types/API/eval/dependency checks are running.
CI45012559308 at6e0edba: lint/types PASS, API81/indexer52/eval33 PASS,93.31% API
coverage,31+3 strict manifests PASS,3 builds PASS; UI scan FAIL, other scans canceled,
e2e skipped. Final collection-isolation test is the additional53rd indexer test.
Git fetch confirms dev2 remains3dff736; no partner changes were overwritten. Existing
PROJECT_DOCUMENTATION.md remains untracked and untouched. Scope/handoff docs updated;
existing A2 measurements remain historical and must not be quoted as A3 reruns.
Next: final check evidence and partner review. HM/CO requests remain unacknowledged.

### 22 November 2026 - Rayyan - Phase 1 stopped at scoped exit
Status: IMPLEMENTED/OFFLINE VERIFIED; partner review and runtime proof PENDING.
Final codebef0283 fixes four-check diagnostics during an embedding outage and reports
an interrupted input honestly. Native35 tests PASS, source hashes committed.
Final CI45013535692: Ruff, API/pipeline mypy, API81/indexer54/eval33 tests PASS;
93.31% app coverage;31 production+3 standalone schemas PASS; all3 image builds PASS;
API/indexer scans PASS. UI scan still FAIL (6 fixable findings), quality FAIL, e2e
SKIPPED. Exact job state/URLs saved in eval/results/phase1/ci-summary.json.
WSL recovered without repair: Python3.12.3 local lint/types/API/eval/53 earlier
indexer tests and pip check PASS. Final extra outage test passed in CI. Docker daemon
remains unavailable; no live model, cluster, threshold or persistence proof claimed.
Report: docs/assignment-3/phase-reports/PHASE-1-REPORT.md. ADR0005/runbook/current
corpus/pipeline/architecture/AI records updated. A2 reports are explicitly historical.
PR6 remains draft to dev2; no merge/approval/main change. Remote dev2 still3dff736.
Only original PROJECT_DOCUMENTATION.md remains untracked/excluded. HM-01..HM-10,
CO-05/06/09 review and genuine human requirements remain pending, not invented.
Moez: review the published diff/contracts and address UI security separately. Run
live lifecycle/Jobs on the approved host in Phase3 and return original evidence.
Rayyan's next authorized implementation prompt: PHASE-2-IMPLEMENTATION-PROMPT.md,
after the Phase1 contract handoff. Phase2/3 have not started automatically.

### 22 November 2026 - Rayyan - Phase 2 authorized while review is pending
User explicitly authorized Phase2 without waiting for Moez's Phase1 handoff review.
Branch codex/a3-phase-2 starts at Phase1 head8161605, preserving all earlier work;
PROJECT_DOCUMENTATION.md stays untracked/excluded. No approval/merge is assumed.
CO-07..11 shared-edit notice: implement request-scoped traces, exact sanitized model
attempt evidence, cache provenance, bounded JSONL/tools/metrics and trace PVC wiring.
Narrow eval/gate/release/CI fixes in the supplied Phase2 prompt are authorized;
announce this before touching eval/ or release files. Golden human provenance remains
honest; no automated question is marked handwritten or human-reviewed. Existing
interfaces remain additive. Parallel implementation tasks share the same branch;
only the root agent commits/pushes and coordinates overlapping files.
Requests requiring approved host access, real measurements, genuine human labels,
class paper/due date, and partner review remain assigned to Moez in HM records.
Phase3 experiments/submission are not authorized by this turn.

### 22 November 2026 - Rayyan - Phase 2 implementation handoff
Status: IMPLEMENTED; final CI verification in progress; human/runtime work pending.
Commits aeadb93,0b172bc,fd5d034,831f3b9,fed6949 on codex/a3-phase-2. Draft PR7 is
stacked on codex/a3-phase-1 to avoid silently merging unreviewed PR6; after PR6 lands,
retarget PR7 to dev2 through normal review. No partner approval has been assumed.
CO-07/08: additive AskResponse.evidence has actual sanitized transport attempts,
context/hash, collection/generation/model digest, pipeline/seed and original cached
answer provenance. The judge reads that immutable evidence, not later Chroma text.
CO-09/10: versioned immutable configs and evaluated receipts bind template/index/Job;
release.py undo also reconciles the scheduled writer. Raw kubectl undo alone is not
advertised as sufficient. --force is removed; deliberate bad-release evidence must
not be manufactured by bypassing a failing gate. Baselines are explicit and exclusive.
CO-11: four image builds/scans, dev2/feature checks and standalone schemas added.
A ConfigMap placement defect introduced here failed strict CI and was corrected;
local strict32 production+9 separate objects now pass. Existing UI scan issue remains
HM-10. No scan or test was weakened. Eval fixtures/tests were updated for the additive
evidence contract and missing uncited-answer measurements now fail closed.
Initial baseline indexer54 PASS; later new corpus provenance test makes55. Local
API89 PASS/90.92% coverage before the last3 trace tests; final CI checks all92.
Eval39 PASS before the final missing-level test; final CI checks40.11 focused trace
tests PASS. Both mypy checks, Ruff and pip check passed at recorded revisions.
Golden check still fails34 issues (15 questions,13 answerable,2 unanswerable,0 hard;
no verified human origin/review/physical pages). Those flags were not fabricated.
HM-01..09 remain pending. Moez: supply/verify the real human golden questions/reviews
and hand answer labels; supply paper/deadline and approved host evidence. Run PartB
and return a real failure trace for D5; if Rayyan cannot access it, perform the trace-
only five-line diagnosis and label its actual human/agent provenance. Run the PVC,
release/undo/Job demonstrations and measured thresholds/resources in Phase3. These
host/human tasks are assigned to you, not silently claimed complete by Rayyan.
Root continuation completed the worker drafts; the transient worker usage limit is
not being used to declare feasible coding work complete without checks.

CO-11 final verification adjustment: disable matrix fail-fast for vulnerability scans
only, so the pre-existing UI failure cannot cancel API/indexer/eval scans. All scans
still fail on fixable HIGH/CRITICAL and quality still requires every scan. This
collects evidence without suppressing findings. CI45029477098 built all4 images and
passed lint/types/tests/41 strict resources; scans other than UI were canceled.

Offline replay artifacts are committed under traces/phase2-offline (explicit mocked
transport/fixture labels) and eval/results/phase2/offline-trace-summary.json. They are
not live model, PartB/D5 or Kubernetes evidence. Additional import-collision check:
from eval cwd, pytest --cov=query_coverage ran40 tests successfully with the real
coverage plugin; measured query_coverage coverage58%, separate from API coverage.
A final metric-range regression rejects impossible component rates,17 gate tests PASS.
CI45029781365 at2b2e410:92 API/55 indexer/40 eval tests,94.29% app coverage, all4
builds,32+9 strict resources PASS; API/indexer/eval scans PASS, UI scan FAIL, quality
FAIL and e2e SKIPPED. Final metric-range case adds one eval test for the next code
revision. No scanned pass is claimed for an unbuilt later image.

Final review also pinned module sampling to the exact collection that served the
query rows and rejects generation changes during typo-noise comparisons. This avoids
a late reindex mixing module/noise measurements with older request provenance.
Scoped suite tests13 PASS. No new real measurement is claimed.

### 22 November 2026 - Rayyan - Phase 2 final verified handoff / STOP
Final code215fd68, CI45030554656:92 API/55 indexer/42 eval tests PASS,94.29% app
coverage, Ruff/both mypy PASS,32+9 strict resources PASS, all4 builds PASS, API/
indexer/eval scans PASS. Existing UI scan6 findings FAIL; quality FAIL, e2e SKIPPED.
Exact states in eval/results/phase2/ci-summary.json; offline-only trace/replay/summary
artifacts committed and explicitly labeled. No live model or cluster claim.
Report: docs/assignment-3/phase-reports/PHASE-2-REPORT.md. PR7 remains draft stacked
on PR6; final source and evidence pushed under Rayyan's account, no merge/main change.
PROJECT_DOCUMENTATION.md is untouched/excluded; fetched dev2 remains3dff736.
All feasible scoped Phase2 coding is implemented/verified. Moez: handle the remaining
human-source provenance/labels, class paper/due date, UI fix/review and approved-host
Phase3 runs/screenshots/resources; supply the real trace or perform the D5 diagnosis
with honest provenance. Both members' actual attendance/explanation remains required.
Rayyan can authorize PHASE-3-IMPLEMENTATION-PROMPT.md when its entry evidence/access
is available. Phase3 was not started automatically and A3 is not declared finished.

### 22 November 2026 - Rayyan - final Phase 3 authorization and ownership transfer
Rayyan explicitly says this is his last prompt and requests no future work allocation
to him. Effective now, all outstanding project implementation/integration, host runs,
data preparation, report finalization, evidence capture, reviews/merge coordination
and submission preparation are assigned to Moez/his agent. No further project work
is expected from Rayyan under this handoff. This transfers ownership; it does not
turn unmet assignment requirements into completed work or claim Moez accepted it.
The official requirement that BOTH students personally attend and explain remains;
no file can delegate or certify Rayyan's actual attendance/understanding for him.
Phase3 starts from01360b3 on codex/a3-phase-3. Existing untracked user documentation
is preserved. Docker remains stopped, C has only about195MiB free, and current
Minikube endpoint refuses connection. No approved connection to Moez's host supplied.
Independent authorized work: fix the verified UI image vulnerability with a new
upstream digest, rerun all CI checks, prepare complete editable report/handoff draft,
consolidate Moez's exact run/submission checklist and final acceptance record.
Do not fabricate human labels, real runs/screenshots or reviewer approval. No Docker
socket repair or destructive cluster operation is authorized/performed here.
