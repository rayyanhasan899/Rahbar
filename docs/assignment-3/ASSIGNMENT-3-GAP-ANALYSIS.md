# Assignment 3 gap analysis

Owner: Rayyan Hassan. Evidence date: 22 November 2026.
This is an AI-assisted planning analysis, not a claim of handwritten implementation.

## Authority and scope

The five-page Assignment_03.pdf is authoritative. Relevant headings are Instructions,
Submission Guidelines, Tasks Overview, Parts A through G, and Submission.
It specifies 185 marks, two students, own-run measurements, a Kubernetes demo,
repository plus report PDF (eight main pages maximum, screenshot appendix excluded).
Both members must explain every part. No due date is visible; confirm it separately.

The earlier Assignment 02 PDF and STARTER.md define the existing baseline, not new
A3 completion. The downloaded Assignment_3 Rubric.pdf is for a job application
package, not this course's RAGOps work. The exact classroom paper version is not
available locally; a 2025 arXiv record and a 2026 SSRN entry exist. Obtain the class
paper before final Figure 3/Table 2 claims.

Preserve the A2 API contract, source/page/version metadata, model compatibility,
grounding/citation/abstention checks, cache safety, one ingestion writer, truthful
probes, persistent stores, network isolation, non-root workloads and protected-main
reviewed release workflow.

## Fresh source reconciliation

- Local dev 3665108: tracked files clean before planning, untracked
  PROJECT_DOCUMENTATION.md preserved. This is an A2 guide, not an A3 plan.
- Local main is an old initial revision; local origin/main is also stale. Do not
  infer current GitHub state from those references.
- GitHub main e92fbe7 includes the later portfolio documentation.
- GitHub dev2 3dff736 is five commits ahead of main, zero behind, 41 changed paths.
- All five A3 commit author records identify AbdulMoez-24i-3048-SE-B,
  i243048@isb.nu.edu.pk, on 21 November. This establishes metadata, not who typed
  the code or operated an assistant.
- No branch switch, fetch, merge, reset or remote mutation was performed for planning.

| Commit | Actual scope |
|---|---|
| 9c545e0 | A3 plan, host allocation and AI/manual task files |
| e7d3530 | Three-level suite, conversion/validation/generation tools and API seed support |
| 843e21f | Configurable release gate |
| ae988e6 | Coverage analysis and exit status |
| 3dff736 | Eval image/Job/PVC/ConfigMap, candidate Deployment/Service and release script |

## Already implemented: reuse, do not duplicate

On dev2, eval/common.py implements recall, MRR, nDCG, cosine and service helpers.
module_embedding.py measures pair similarity, speed and repeated embedding.
end_to_end.py judges support and aggregates citations, abstention and latency.
suite.py orchestrates and compares runs. golden_check.py, convert_golden.py and
synth_questions.py manage draft test data. coverage.py calculates nearest-question
coverage and uncovered-topic groups. gate.py applies thresholds.
scripts/release.py creates a candidate from the CronJob template and promotes it.
k8s/eval-job.yaml, eval/ PVC/config/shell objects and candidate/api-candidate.yaml
exist. Providers/configuration accept SEED. These are implemented scaffolds,
not verified complete assignment demonstrations.

A2 already has OCR/HTML extraction, cleaning, structured lexical-token chunks,
bounded embedding batches, Chroma 1.0.12, UUID generation publication, shared writer
lock, Redis cache, injection guard, schema/citation retry and Kubernetes resources.
run_pipeline still extracts/chunks/embeds the whole corpus. There is no A3
verification/quarantine/ledger/rollback implementation or complete persisted trace.

## Requirement traceability snapshot

P means partial, N not started, U cannot verify. No item is complete merely because
a similarly named module exists. A2 facilities count as partial only where they
provide actual reusable behavior.

| Item | Status | Existing evidence | Gap / owner |
|---|---|---|---|
| A1 four checks, reasons, quarantine/report | N | extract.py only | Verification/lifecycle; Rayyan |
| A2 incremental changed/deleted/archive/rollback | N | full rebuild + active pointer | Ledger, zero-embed reruns, reconciliation; Rayyan |
| Batch B >=10 planted documents | N | absent | Owned fixtures/generator/expected outcomes; Rayyan |
| B golden set and human provenance | P | golden.jsonl/check/converter | Counts, physical pages, human work; both |
| B module measurements | P | module_embedding.py; 15+15 draft pairs | Actual results/review; Moez |
| B component/noise measurements | P | common.py + typo path | Real golden/noise outputs; Moez |
| B end-to-end + human judge agreement | P | end_to_end.py | Real outputs and >=8 human labels; both |
| B stochasticity | P | seed + compare | Two controlled runs/differences; Moez |
| B one-command timestamped summary | P | suite.py | Validation/integration and real output; Moez |
| C1 baseline/candidate all three levels | P | candidate script | Same-corpus controlled experiment; Moez |
| C2 justified gate/fail/pass | P | gate.py + null thresholds | Harden, justify and demonstrate; Moez |
| C3 Kubernetes release/undo | P | release.py | Real proof; both |
| D1 full trace per query | N | partial A2 logs | Complete durable trace; Rayyan |
| D2 exact prompt/context by trace ID | N | absent | Reconstruction/hash/provenance; Rayyan |
| D3 distributions/rates/stage p95/window summary | P | existing counters/histograms | Missing metrics and summary; Rayyan |
| D4 rail action in trace + Batch B test | P | guard.py and flags | Trace event and retrieved poison demo; Rayyan |
| D5 trace-only diagnosis, five lines | N | absent | A real Part B failure trace; Rayyan |
| E1 >=40 queries, >=12 uncovered | N | absent | Truthful workload dataset; both |
| E2 nearest golden/coverage/topics | P | coverage.py | Inputs, justified threshold and run; Moez |
| E3 suite after Batch B drift | N | depends on A | Real before/after explanation; both |
| E4 >=6 questions and improved coverage/failing exit | P | coverage exit code | New dataset and measured improvement; both |
| F1 deployment and persistent lake/archive/quarantine | P | A2 API/store/PVCs | New lake storage/persistence proof; Rayyan |
| F2 verified ingest Job/Cron, eval Job/PVC/gate map | P | new eval objects + old indexer | Integrate A; gate-map outcome demo; both |
| F3 staging/gate/rolling release/undo trace | P | candidate resources | Ingestion/config consistency and real proof; both |
| F4 stdout + volume traces, port-forward metrics | P | stdout/metrics | Durable traces and proof; Rayyan |
| F5 measured API/store/Job resources | P | limits/requests, provisional eval values | New measurements/report; Moez |
| G1 Figure 3 stage/file/missing-work table | P | draft PLAN table | Align with final code/paper; both |
| G2 five qualities table | N | allocation only | Measures/thresholds/evidence; both |
| G3 results/figures/release decision | N | no A3 run results | Real evidence/report; both |
| G4 six short answers | N | absent | Actual findings, not generic text; both |
| G5 contribution table + short AI statement | N | A2 disclosure only | Actual A3 actions/tool use; both |
| Submission repo/results/traces/both contributors | P | code/k8s; results README only | A3 evidence and actual contributions; both |
| README exact commands A-F | P | A/D marked to be added | End-to-end tested commands; both |
| Submission PDF/screenshots | N | not found | <=8 pages plus uncropped appendix; both |
| Both explain/live unseen-batch demo | U | intentions only | Joint rehearsal/attendance; both |
| Assigned paper/version fidelity | U | exact class copy missing | Supply class copy; Moez/user |

Totals: 36 items, complete 0, partial 21, not started 13, blocked 0, unverifiable 2.
Readiness index = (0 + 0.5*21)/36 = 29.17%. This is not a mark prediction,
time estimate or claim that only 29% of source code exists. Environment blockers
are recorded separately from missing implementation.

## Specific defects and coordination issues

1. golden.jsonl has 15 rows: 13 answerable, two unanswerable, no hard labels,
   no human labels or reviewed-synthetic labels. Ground-truth physical pages are null.
   Its own validator reports 34 issues. Do not turn old agent-written questions into
   human questions or accept retrieved page candidates as independent ground truth.
2. suite.py reads golden data without invoking golden_check before service calls.
   It must reject invalid evaluation inputs before emitting authoritative measurements.
3. gate YAML and ConfigMap leave faithfulness/latency values null deliberately.
   This is a pending calibration task, not a passing gate.
4. gate.number accepts nonfinite values. A read-only probe confirmed inf/-inf
   thresholds could be accepted. Validate finiteness, ranges, missing values,
   citation completeness and baseline/run comparability.
5. eval/job.py bootstraps the first run as baseline. Candidate runs on an empty PVC
   must not quietly become their own baseline. Baseline creation must be explicit.
6. release.promote changes only live API CHROMA_COLLECTION; the scheduled ingestion
   configuration can continue writing the old collection/chunking. Plan release and
   rollback of the reader AND correct future-writer configuration.
7. The proposed in-place delete-before-embed A2 algorithm can destroy working evidence
   on failure. Preserve A2 safe publication/recovery, while reusing unchanged vectors
   and proving zero embedding calls on identical input.
8. A1 says failed documents quarantine; the plan archives recency-only failures.
   Reconcile verified historical archival with failed incoming-document quarantine.
9. A2 permitted explicit old-year retrieval; the plan excludes every archived version.
   Preserve baseline behavior or document/review a deliberate contract change and
   version the golden expectations. Do not rewrite a baseline to hide regression.
10. The suite fetches raw chunks after the answer from the active collection. Those
    may differ from sanitized context or a generation used before a pointer change.
    Judges and traces must use exact request-time evidence and version provenance.
11. SEED is not included in existing cache identity. Prevent cached/stale answers
    contaminating seeded comparisons; prefer scoped bypass/clear over Redis FLUSHALL.
12. test_coverage.py imports coverage, which can collide with pytest-cov's package.
    This is a static risk, not a reproduced pytest failure.
13. CI only pushes on dev, not dev2; the original three-image matrix and base
    manifest validation do not prove the new eval image/separate manifests work.
14. Eval image uses a mutable dev tag and provisional resource values.
15. Trace cache hits must identify the original answer/prompt provenance. Do not
    fabricate a model call or a new prompt for a cached answer.

## Verification and confidence

Phase 1 audit performed native AST checks on 66 local and 15 remote Python files,
five focused pure metric/gate probes, the golden validation and local Kustomize
rendering (909 lines). Historical A2 results: 15 questions, recall@5 11/13,
citation validity 1, both mandatory abstentions refused, eight cited answers.
Historical API evidence records 80 tests and 93.39% coverage; not a fresh A3 pass.

Full pytest did not start: WSL returned
Wsl/Service/CreateInstance/E_UNEXPECTED. Native Python lacks pytest.
No fresh Ruff/mypy/new-image build/new strict manifest validation/real cluster
evaluation is claimed. Repair environment separately or use approved CI/Moez's host;
do not install dependencies or change host configuration merely to plan.

## Contribution evidence and limits

A2 Rayyan-associated commits were substantially automation-assisted, explicitly
recorded in docs/AI-USAGE.md. Moez's A2 answer/provider/cache work is recorded as
Claude-assisted. Preserve that disclosure and every author's history.
All five new A3 Git author records name Moez; that does not prove handwritten code
or the exact assistant/operator. Embedding pairs explicitly say assistant-drafted.
No completed A3 implementation by Rayyan is evidenced at this snapshot.
Task allocation is intention, not proof of delivery. Do not fabricate personal
debugging time, human questions/reviews, screenshots, contribution percentages
or partner approval.

