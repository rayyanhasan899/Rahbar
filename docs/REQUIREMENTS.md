# Requirement traceability — Day 1

Status is scoped to observed evidence, not file existence. The assignment PDF
controls the requirements; the submission checker is only a mechanical lint.
Deadline: 8 November 2026, 23:59 PKT. No weighted rubric table was supplied.

| PDF requirement | Implementation / evidence | Day 1 status | Verification / remaining dependency |
|---|---|---|---|
| §2 six documents, forty pages, seven corpus properties | sources, MANIFEST, CORPUS, extraction audit | Verified selected eight documents; six PDFs 194 pages | Download hashes, page counts, policy comparison; final human corpus review |
| §2 genuine changed versions | golden q09/q10, version-comparison.md | Verified clause 4.25 difference | Old p16 visually checked, current clause read |
| §2 scanned PDF/OCR | extract.py, extraction-audit.json | All eight startup-policy pages OCRed | Six other pages remain empty; disclose limitations |
| §2 tables/long definitions/exact/absent | CORPUS, table-audit.json, golden | Implemented/documented | Detailed table and absent-topic human review remains |
| §2 public sources, manifest, polite fetch, no PDF commit | fetch.py, sources.yaml, .gitignore | Verified downloads and tracked-file exclusions | Reverify hashes before final submission |
| §2 name corpus in first PR | GitHub PR #1 | Verified draft PR | Pair/instructor review still needed |
| §3.1 extract/clean/chunk/embed/store | indexer/pipeline | Implemented; offline tests pass | Real embedding/storage experiment evidence recorded separately |
| §3.1 structure/overlap/page/version metadata | chunk.py, models.py, tests | Unit-tested | OCR section recognition remains heuristic |
| §3.1 three measured configurations/amplification | scripts/chunk_experiment.py, eval/chunk-experiments.json | Three runs verified: 84.6154% recall@5 each | 647/565/536 chunks; retune augmented table extraction before final shipping |
| §3.2 validation 3–500 | schemas.py, starter tests | Tested | Preserve response compatibility |
| §3.2 real retrieval/current-historical filtering | retrieval/chroma.py | Implemented initial reader | Broader version-language tests Day 2 |
| §3.2 turns/follow-ups | services and request contract | Not implemented | Day 2 compatible conversation design |
| §3.3 semantic cache/threshold tests/exclusions | Redis resource; PIPELINE notes | Infrastructure only | Day 2 algorithm, measured thresholds and tests |
| §3.3 reindex cache invalidation | Published generation metadata | Mechanism supplied | Day 2 cache hit integration and invalidation demo |
| §3.4 schema/retry/fallback/relevance/citations | Answer schema/stub supplied | Not production-complete | Day 2 real provider and negative tests |
| §3.4 poison chunk and untrusted output | Fixture already poisoned; safe textContent UI | Test pending | Index poisoned fixture and assert refusal to obey |
| §3.5 pluggable fully supported provider/temperature | Existing interface; model installed | Stub only | Day 2 real constrained provider; temperature justification |
| §4.1 namespace/API x3/UI | k8s/base and cluster evidence | Running dummy stack | Final SHA images Day 3 |
| §4.1 Chroma StatefulSet/PVC, Redis/PVC | StatefulSet, Deployment, bound claims | Running | Data deletion/persistence demo still pending |
| §4.1 Job/CronJob, retries, weekly schedule | Job completed; weekly CronJob suspended | Dummy bootstrap verified | Supply real corpus, remove dummy, enable weekly schedule |
| §4.1 four ClusterIP Services/Ingress | services, ingress; ingress-stub-smoke.json | Verified stub answer through Ingress | Real grounded answer remains |
| §4.1 ConfigMap/Secret | configmap, unapplied placeholder | Implemented scaffold | Measured thresholds and optional runtime key |
| §4.2 one writer/no API ingestion | run.py lock; store.py pointer; ADR0001 | Implemented/tested failure path | Concurrent cutover load evidence Day 2 |
| §4.3 probes and truthful readiness | health.py, API probes/tests | Dependency checks tested | Final dependency-outage cluster demo pending |
| §4.4 shared pin/dimension conflict | collection metadata, active reader/startup check | Implemented | Explicit cluster pin-mismatch demo Day 2/3 |
| §4.5 every container requests/limits, metrics | manifests; kubectl top evidence | Initial measured output captured | Tune limits to observed load; capture indexer peak |
| §4.5 HPA 3–8, numeric CPU metric | HPA, metrics-server | Final snapshot: 2%/70%, min3/max8, three replicas | Temporary diagnostic cap was restored; startup failures preserved separately |
| §4.6 maxSurge1/maxUnavailable0/grace/preStop | API manifest | Applied | Visible change/rollback/endpoints demonstrations |
| §4.7 ServiceAccounts/nonroot/readonly/drop/token | all workload manifests | Applied | Runtime/security audit before final submission |
| §4.7 deny-by-default, UI cannot reach Chroma | networkpolicy.yaml, Calico, day1-network-final.txt | UI to API allowed; UI to Chroma blocked with DNS resolving | Selected real-model egress remains Day 2 |
| §4.7 no secrets/history/untrusted eval | ignore rules, placeholder, UI | No real secret added | Final history scan; never weaken policies |
| §4.8 JSON IDs/request logging/basic metrics | existing middleware; answer logs | Partial | Retrieval/generation/cache/token counters Day 2 |
| §5.1 golden 8/2/2/2/1 before tuning | golden.yaml, commit d7b5e88 | Verified | Human correctness review of final answers |
| §§5.2–5.4 recall/citations/abstention/gates | run_eval.py, eight evaluator tests | Unit-tested | Real generation results/baseline not yet established |
| §5.5 four deliberate failures | FAILURE-ANALYSIS template | Pending | Controlled observed experiments Day 3 |
| §6 dev/main PR/one approval/checks | dev pushed, draft PR #1 | Partial | Settings approval and genuine partner review |
| §6 CI lint/test/60%/manifests/build | ci.yml, local tests and validator | Seven Day 1 jobs passed in run 41976761836 | Final checkpoint CI linked from PR; bootstrap is not real e2e evaluation |
| §6 Trivy/e2e-eval regression gate | bootstrap job only | Pending Day 2 | Bootstrap is not the real quality gate |
| §6 CD needs/SHA/Docker Hub/ephemeral deployment | Not yet implemented | Pending Day 3 | Secure registry secrets and real successful run |
| §7 seven evidence-based engineering answers | ENGINEERING-NOTES template | Pending | Real metrics/line refs/debugging history |
| §10 README/architecture/four ADRs/AI/evidence/LICENSE | README/architecture/two ADRs/AI notes | Day 1 subset | Remaining ADRs, notes, license, screenshot |
| §8 Classroom repository/CD/images/results/baseline | Repository/PR exist | Not submission-ready | Final links, committed results and checker |

Automatic deductions tracked for final audit: history secrets -20; real base64
Secret -15; API-startup indexing / fabricated citation / answered must-abstain
-10 each; persistence/exposure or silent embedding mismatch -8; missing
requests/HPA unknown or ungated publishing/latest deployment -6; default
namespace or broken clean-clone apply order -5; direct main push -4.
