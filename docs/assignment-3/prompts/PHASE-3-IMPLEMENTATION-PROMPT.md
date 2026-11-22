# Execute Phase 3 - real Kubernetes evidence and submission readiness

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


## Entry condition, objective and scope

Inspect actual Phase1/Phase2 implementations and checks, not only their reports.
This phase executes T10-T12 and finishes measured D5/G/submission deliverables.
Official scope: runtime verification of A-F, report G1-G5, README commands and
Submission screenshots/repository/PDF. Fix real defects through tested scoped commits
when necessary; do not rewrite working modules or start optional enhancements.

Read current k8s/README.md, docs/a3/MANUAL files, trace tools, eval suite/gate/release,
golden provenance and COMMUNICATION.md. Confirm Moez's planned16GB machine is actually
available and that approved access exists. If not, supply exact commands/evidence
requests in the ledger and continue independent report/tool checks. Do not fabricate
remote execution or repeatedly retry an inaccessible host as if it were progress.

## Ordered real experiment campaign

1. Confirm official due date/class paper, both final names/roll numbers, genuine
   human question/review/judge records. Never relabel agent drafts as handwritten.
   Verify current Git heads, image SHAs, dependency locks, model digests and corpus/
   golden/config hashes. Use existing authenticated accounts securely.
2. On the approved GROUP Kubernetes cluster, build/load immutable API/indexer/UI/eval
   images; apply namespace/storage/services/policies/dependencies, run verified
   ingestion, then wait for API/UI readiness. Kubernetes is mandatory; Docker-only
   or stub-answer runs cannot serve as real A3 generation proof.
3. Run A on Batch A and again unchanged: log actual zero chunks/calls embedded.
   Demonstrate changed-only replacement, deleted-doc counts without orphans, archive/
   restore, rejected-update preservation and storage surviving pod restarts.
   Run reproducible Batch B >=10 documents and preserve four-check reasons/report.
4. Establish the baseline explicitly. Run whole B twice at the same seed with
   controlled cache/model/config and report every metric difference. Include >=15
   paraphrase and >=15 unrelated pairs, gap, embedding timing and determinism;
   recall@3/@5/MRR/nDCG@5 plus noise deltas; faithfulness/citations/abstention/p50/p95.
   Independently obtain >=8 hand answer labels before showing judge verdicts;
   compute agreement honestly, including disagreements and missing labels.
5. Select ONE C change, comparing baseline/candidate on equivalent data and labels
   at all three levels. Choose finite gate thresholds from the measured baseline,
   justify them, then demonstrate one fail and one pass. Retain negative results.
   Changing gate ConfigMap alone must change an eval Job's outcome without rebuilding.
6. Run candidates with separate Deployment/Service/collection. Prove a failed
   candidate never changes the live rollout. Promote a passing candidate through
   maxUnavailable0 rolling update and observe rollout status. For an isolated,
   authorized bad-release demo, roll it out then undo; ask a new question and capture
   the trace showing the restored collection AND embedding version. Verify future
   scheduled ingestion configuration is also coherent after promotion and undo.
7. Demonstrate D: complete JSON trace in kubectl logs and persistent volume, exact
   prompt/context reconstruction and hash check, window summary, metrics port-forward,
   actual guardrail action for retrieved Batch B injection. Select an actual wrong/
   refused Part B answer and write D5's FIVE lines using its trace only. If the trace
   lacks the evidence, improve/retest instrumentation instead of consulting unrelated
   logs and pretending it was a trace-only diagnosis.
8. E: >=40 user-style queries (about28 in-domain, >=12 uncovered), nearest golden
   similarity/share with justified thresholds, uncovered topics. Re-run B after
   Batch B drift and explain document/version effects. Add >=6 new golden questions,
   preserve the before/after versions, demonstrate coverage rises and below-threshold
   nonzero exit. Do not lower thresholds or copy live queries blindly just to pass.
9. F5: collect repeated actual resource measurements during API/vector-store/
   ingestion/evaluation work. Record sampled peak, limit and margin; do not diagnose
   every exit137 as OOM without container reason. Set justified requests/limits,
   retest after changes and keep measurements in report/results.
10. Save original result files/reports under eval/results/, trace samples/summaries
    under traces/, all manifests under k8s/. Do not commit third-party downloaded
    PDFs or full proprietary text. Review traces for secrets/privacy before sharing.

## Mandatory screenshot and report checklist

Capture actual terminal UI with command AND output, uncropped, from the group's own
cluster/runs. Never recreate terminal text as an image or reuse A2 screenshots as A3.
Label appendix items by part/item:
- A: Batch B verification with all checks/reasons; unchanged second run zero embedding.
- B: all three-level evaluation summary.
- C: gate failing and passing.
- D: complete trace; reconstruction command and output.
- E: coverage before and after new questions.
- F: kubectl get all,pvc,configmap,cronjob,job -n rahbar; completed ingestion/eval Job
  logs; ConfigMap-only changed gate result; rollout status/undo and restored trace.

Prepare a PDF with at most EIGHT main pages plus screenshot appendix. First page
lists both members' verified names/roll numbers. Include:
G1 Figure3 stage/action/file/missing-work table;
G2 five Table2 qualities (adaptability, monitorability, observability, traceability,
reliability) with measures/thresholds/evidence;
G3 actual A-F results and release/reject decision;
G4 all six exact short answers, grounded in actual findings;
G5 true contribution table and 2-3-line AI statement.
Use current PDF authoring guidance, render/reopen/check page count and visually
inspect every page/screenshot. Keep editable report source and a traceable results
manifest. No AI-generated human learning/experience claim.

## Final verification, rollback and Definition of Done

Run the current Phase2 lint/types/offline tests/coverage>=60/pip check, strict validation
for all new objects and all four builds/scans. The old scripts/check_submission.py
can check A2 regressions but is NOT an A3 grader; do not edit it to make results pass.
Run a clean checkout on a distinct disposable cluster when approved; never execute
the plan's minikube delete against the user's existing cluster without specific
authorization. Rehearse live eval Job, trace tool and genuinely unseen batch ingestion.
Both humans must attend and explain the whole system; automation cannot attend as them.

Retain previous config/collection/model revisions, immutable baseline and negative
experiments; normal reviewed revert/rollback only. No direct main push or invented
partner review. Push all required results/traces/manifests/report through meaningful
Rayyan-authored milestones and reviewed PRs. Preserve Moez's contributions.
If existing CD runs after merge, verify what the actual merge SHA built/deployed;
do not substitute obsolete image tags. A3 submission is repository URL + report PDF,
not merely the old A2 four-link checklist. Do not submit Classroom without a separate
explicit instruction.

Definition of Done: every official requirement has implementation and real verification,
all mandatory output files and screenshots are accessible in the reviewed repository,
PDF meets page/legibility rules, human provenance and contributions are genuine, and
clean-cluster/demo rehearsal succeeds. Otherwise report each remaining requirement as
BLOCKED/NOT VERIFIED with exact owner/action/evidence; do not claim full completion.

## Required end-of-phase report and hard stop

Update COMMUNICATION.md, requirement traceability and assistance/contribution records
with actual actions. Report completed files/features, commands and real outcomes,
regressions, remaining blockers, proposed partner actions, commits/push/PR state and
the precise next phase entry condition. Clearly distinguish IMPLEMENTED from VERIFIED.
Do not publish secrets or full private records in evidence.
STOP at this phase's exit condition. Do not start the next phase automatically.
If a requirement remains blocked, say so; do not declare full assignment completion.

