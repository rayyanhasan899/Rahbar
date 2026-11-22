# Assignment 3 shared communication and handoff

Project owner for this work: Rayyan Hassan / rayyanhasan899.
Partner: Moez / AbdulMoez-24i-3048-SE-B.
Created: 22 November 2026, Asia/Karachi. Status: PHASE 1 IMPLEMENTED; VERIFICATION IN PROGRESS.

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

## Current verified state

- Local dev: 3665108; untracked PROJECT_DOCUMENTATION.md must be preserved.
- GitHub main: e92fbe7; GitHub dev2: 3dff736 (five A3 commits ahead).
- Moez's implemented scaffolds: B suite/golden tooling, C gate, E coverage,
  F evaluation objects/candidate release, provider SEED support.
- Rayyan's A/D and ingestion/trace F implementation: NOT STARTED in inspected dev2.
- A3 results, traces, human review records and report PDF: not supplied/verified.
- Full unit testing is blocked on Rayyan's current WSL startup error E_UNEXPECTED;
  do not replace the environment or call saved A2 test output a new pass.
- These new planning documents do not change application code or represent a phase run.

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
