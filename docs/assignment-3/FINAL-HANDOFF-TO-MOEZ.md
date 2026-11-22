# FINAL HANDOFF TO MOEZ - Rayyan's project allocation is closed

Effective22 November2026, at Rayyan Hassan's explicit instruction:

> I will no longer do any project work. My work is finished for this handoff.
> All remaining project work is now assigned to Moez/his agent and is no longer
> allocated to me.

Rayyan's ongoing implementation/report/execution allocation is CLOSED. No additional
prompt, coding, host operation, review coordination or report completion is expected
from him. This transfers ownership of unfinished tasks; it does not mark unfinished
assignment requirements complete, imply Moez accepted them, or invent human evidence.
The official requirement that BOTH members personally attend and explain every part
still applies. Actual attendance/understanding cannot be certified or delegated by
this file. All remaining project coordination to satisfy requirements belongs to Moez.

## Start here

1. Fetch the existing remote and preserve your own dirty/untracked files.
2. Read this file, COMMUNICATION.md and phase-reports/PHASE-3-REPORT.md.
3. Review PR6 (Phase1), PR7 (Phase2, stacked on Phase1) and the Phase3 PR. After each
   dependency lands, retarget the next to dev2. Use genuine review; no force/reset/
   main push or invented approval. The final feature branch contains all earlier work.
4. Use the existing repository/locks and k8s/README.md. Do not follow historical
   FLUSHALL, auto-baseline, --force release or destructive cluster-delete instructions.
5. The8-page report/report-content.json + build_report.py + HANDOFF-DRAFT.pdf are an
   editable head start, NOT the final submission. Every PDF page is marked draft.

## Already delivered by Rayyan's authorized agent

Verified ingestion/ledger/cache/archive/rollback;13 owned BatchB inputs; trace/replay/
summary/metrics/PVCs; exact-context/seed/cache/provenance gates and coherent release/
undo; offline tests and CI; architecture/ADRs/runbooks. Phase3 additionally patches
nginx to1.30.7 with upstream OCI digest, drafts25 source-grounded synthetic golden
rows,40 user-style queries (28 intended in-domain/12 intended outside),6 coverage
expansion candidates and the report package. Existing partner work and original
untracked PROJECT_DOCUMENTATION.md are preserved. Actual assistance is disclosed.

Current branch: codex/a3-phase-3 (includes Phase1/2). Remote repository:
https://github.com/rayyanhasan899/Rahbar
Full green security-fix run: https://github.com/rayyanhasan899/Rahbar/actions/runs/45033156542
It builds/scans4 images and runs Kubernetes FIXTURE e2e. Answer generation is stubbed;
this is not the required real-corpus A3 measurement/demo evidence. Later evidence
and final source SHA are recorded in PHASE-3-REPORT.md.

## All outstanding work - owner: Moez / his agent

| ID | Action now assigned to Moez | Required completion evidence |
|---|---|---|
| M01 | Confirm due date, exact class paper edition, both verified full names/roll numbers | Paper/version reference and first report page; no guessed identity |
| M02 | Prepare final golden.jsonl: >=25 questions, >=15 answerable, >=5 unanswerable, >=5 hard; genuinely write >=8 HUMAN questions and personally review >=8 synthetic questions | golden_check PASS; source physical pages and true origins/reviewer records |
| M03 | Independently hand-label >=8 actual answers BEFORE looking at judge outputs | hand_labels.jsonl and real judge agreement/confusion output |
| M04 | Provide approved16GB host; verify Docker/WSL/Ollama/model digest/Kubernetes context | Real readiness, model/config/corpus/source-SHA records; no Docker-only demo |
| M05 | Run real BatchA, unchanged rerun, change/delete, invalid-update preservation, archive/pin/unpin, BatchB and PVC survival | Original verification/count/Job JSON/logs, zero actual embeddings and no current orphans |
| M06 | Run B twice with matching fixed seed/cache bypass, module pairs/timing/determinism, retrieval/noise, answer/judge/citation/abstention/latency | Timestamped full result files and stochasticity deltas |
| M07 | Choose ONE chunking change; calibrate finite thresholds from real results; demonstrate fail/pass and ConfigMap-only outcome change | Comparable baseline/candidate provenance, negative/pass receipts, justified thresholds |
| M08 | Stage/promote passing candidate, demonstrate controlled isolated bad release/undo and coherent future writer | Rollout history/status, undo, new restored collection+embedding trace and CronJob config |
| M09 | Capture real D1-D4 trace/stdout/PVC/replay/metrics/rail/window evidence; complete D5 FIVE lines from one real B failure using only its trace | Real samples/reconstruction/summary and5 evidence-grounded lines; no fake diagnosis |
| M10 | Run E2 on provided40 queries; justify thresholds, list topics; E3 afterB; select/review >=6 actual uncovered-topic additions and rerunE4 | Preserved golden-before/after, coverage increase and a below-threshold nonzero exit |
| M11 | Measure CPU/RAM during API/store/indexer/eval work; set/retest justified requests/limits | Repeated kubectl top output, sampled peak/limit/margin; actual termination reason if failure |
| M12 | Capture every official A-F uncropped terminal screenshot with command+output on the group's own cluster | Labeled real appendix images; no recreated terminals, A2 reuse or cropped proof |
| M13 | Finalize all G1-G5 report content/6 short answers, contribution/AI statement, names and screenshots | <=8 main pages plus screenshot appendix; inspect EVERY rendered page |
| M14 | Genuine PR review/merge sequence, final clean checkout and separate approved disposable-cluster/unseen-batch rehearsal | Passing reviewed source, deployed matching SHA, live eval/trace/unseen ingestion; no existing cluster deletion |
| M15 | Commit/push all real results/traces/manifests/final PDF and submit repository+report under the course instructions | Accessible final files/URLs; classroom submission is NOT performed by this session |

No unfinished project item above remains allocated to Rayyan. Historical Rayyan task
lists are superseded for remaining ownership. Do not misstate that ownership transfer
as observed completion or that an agent attended/reviewed/hand-labelled as a person.

## Data work already prepared - do not start from nothing

Read eval/DATA-REVIEW-HANDOFF.md. golden.synthetic-draft.jsonl has25 AI questions
with physical pages7/8/10 independently inspected and cached source SHA recorded.
It fails ONLY the two genuine human-provenance minimums. It does not overwrite your
current golden.jsonl (which still has34 issues). Review/merge chosen drafts and add
actual human questions; never relabel AI questions human. Preserve before/after
versions for the change/drift/coverage experiments. The6 expansion candidates are
NOT already measured uncovered questions or evidence that coverage increased.

## Ordered run-host commands (prerequisites first)

Run from the repository root in your prepared Python3.12 Linux/WSL environment.
Use actual host addresses/source SHA and a verified selected context. These commands
are a handoff, not claims that the blocked laptop executed them.

```bash
git status --short --branch
git fetch origin
# Safely select the reviewed final branch without discarding local work.
python eval/golden_check.py
python corpus/fetch.py --verify
kubectl config current-context
kubectl get nodes
TAG=$(git rev-parse HEAD)
make images TAG="$TAG"
# Bootstrap dependencies -> verified corpus transfer -> indexing -> API readiness:
# use k8s/README.md with your verified Ollama /32 address; keep all4 SHA tags.
```

PartA exact BatchA/B, verify-only, counts, rollback/unpin and evidence-copy commands
are in k8s/README.md. Use all intended input roots; omitted roots are preserved and
missing roots fail safely. Measure real near-duplicate scores before fixing threshold.
Do not call fixture/offline output a real corpus run.

For B, set API ConfigMap SEED equal to suite seed and recreate relevant pods through
the reviewed rollout. The suite bypasses cache itself; NEVER use global FLUSHALL.
Calibrate from an explicitly labeled measurement run, then choose justified gate
values. To create a baseline via eval Job, use LABEL=baseline and CREATE_BASELINE=true
with an absent baseline and calibrated gate ConfigMap. The suite writes a draft
baseline candidate; only passing absolute gates creates the exclusive baseline.
Do not overwrite the baseline or create one from a candidate. Run a second label
with the same seed/config and compare result files.

```bash
python eval/suite.py --compare <run-one.json> <run-two.json>
python eval/end_to_end.py --agreement <run.json> --labels eval/hand_labels.jsonl
python scripts/release.py candidate --name rahbar-cand --chunk-size <chosen-n> --chunk-overlap <chosen-m>
python scripts/release.py promote --name rahbar-cand
python scripts/release.py undo
# After a raw kubectl rollout undo, reconcile before resuming the weekly writer:
python scripts/release.py reconcile --resume
python scripts/trace_tool.py show <real-request-id> <real-trace-path>
python scripts/trace_summary.py --since <ISO-time> --until <ISO-time> <real-trace-path>
python eval/query_coverage.py --live eval/live_queries.jsonl --golden eval/golden.jsonl --threshold <measured-T> --min-share <justified-S>
kubectl top pod -n rahbar --containers
```

Do not put literal angle-bracket placeholders into a shell. Values requiring real
measurements are deliberately not invented here. A candidate stopped by the gate must
not be forced through. Select any bad-release fault only in the approved isolated
demo, preserve prior config, then use controlled undo and verify the new trace.

## Mandatory screenshot / submission index

A: four-check BatchB report and unchanged0. B: all three levels. C: fail+pass gate.
D: complete real trace+replay. E: coverage before+after. F: namespace objects/PVC/
ConfigMaps/CronJob/Jobs, completed ingest/eval logs, ConfigMap-only outcome change,
rollout/undo and restored trace. Each shows the command and full terminal output.
Store original results under eval/results/, real traces under traces/, manifests
under k8s/. Keep secrets/private text/downloaded third-party PDFs out of commits.

Final deliverables are the GitHub repository and FINAL report PDF with appendix,
not the old A2 link checklist and not the current clearly marked handoff draft.
