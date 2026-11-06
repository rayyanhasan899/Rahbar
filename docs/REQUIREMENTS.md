# Day 3 requirement traceability

Deadline: 8 November 2026, 23:59 PKT. The assignment PDF controls requirements.
PASS is scoped to the evidence named here. A script or manifest alone does not
prove live behavior. FAIL means an observed unsuccessful attempt; BLOCKED needs
an external action; NOT VERIFIED means the required observation is still absent.

| Requirement | Status | Implementation and actual evidence | Remaining action |
|---|---|---|---|
| Public corpus >=6 documents/40 pages; seven properties | PASS | Eight selected documents, six PDFs/194 physical pages; corpus/MANIFEST.md, docs/CORPUS.md, version-comparison.md, table/extraction audits | Human review of OCR/table limitations remains prudent |
| URLs, hashes, versions, supersession; no third-party PDFs committed | PASS | Serial fetcher, sources.yaml, manifest; Day 3 PVC 8/8 hashes; remote live fetch 8/8 verified | Preserve source rights/exclusions |
| Golden 8 ordinary/2 version/2 exact/2 abstain/1 injection before tuning | PASS | eval/golden.yaml originated in d7b5e88, independent source/section relevance labels unchanged | None |
| Five stages, OCR, HTML/text/Markdown headings and metadata | PASS | indexer/pipeline; 19 offline tests; fresh local extraction log | Final deployed extraction profile audit still running |
| Three fresh measured chunk configurations/amplification | NOT VERIFIED | Day 1 three real measurements retained in eval/chunk-experiments.json; augmented extraction requires fresh run | Inspect real-audit chunk artifact; replace historical results honestly |
| Shared embedding pin/cosine/stable IDs/repeatable index | PASS | Same model/prefix protocol; Chroma 1.0.12 client/server; store/retrieval checks and tests | Runtime model digest/pin demonstration pending |
| Staging/publication/no API-startup ingestion/serialized writers | PASS | Lock PVC, writer_lock, validated staged collection and generation pointer; multiprocess lock test | Manual/weekly overlap and live cutover observation NOT VERIFIED |
| Current and explicit historical retrieval; turns | PASS | version_filter tests, retained response contract, bounded additive history | Real historical/follow-up answers NOT VERIFIED |
| Shared semantic cache, exclusions/TTL/invalidation | PASS | Cache tests, 113 real embedding comparisons, 0.75 lowest tested zero guarded false hits | Cluster HIT/MISS across publication NOT VERIFIED |
| Schema/one retry/fallback/grounding/citations/injection defense | PASS | Offline model-free tests; sentence attribution and citation checks; safe fallback | Real generation/poisoned-index probe NOT VERIFIED |
| Real LLM fully supported, deliberate temperature | NOT VERIFIED | Ollama/hosted adapters, ConfigMap temperature and bounded timeouts; mocked provider tests | Real cited generation acceptance pending |
| Observability/request IDs/JSON/retrieval/cache/tokens/metrics | PASS | API logging config, metrics and tests | Capture real runtime metrics pending |
| Namespace/API x3/UI/Chroma STS volumeClaimTemplates/Redis PVC | PASS | Strict production manifests; real fixture CI cluster deployments | Real-corpus final runtime snapshot pending |
| Job OnFailure/backoff; same weekly CronJob; four ClusterIP/Ingress | PASS | Base resources + completed real remote indexer; fixture CI Ingress | Verify full real audit report |
| ConfigMap/safe excluded Secret placeholder/dedicated SAs | PASS | Manifests; no real secret committed or values read | None |
| All probes/resources/nonroot/readonly/drop/token security | PASS | Manifests, offline health/startup tests, strict validation | Runtime acceptance and measured memory margin NOT VERIFIED |
| Actual allowed networking/UI->Chroma denied | FAIL | Audit stopped on BusyBox short-name nslookup exit1 despite resolving the correct namespace address | Probe now uses full service DNS; policies unchanged; rerun required |
| Bootstrap dependency/index/API order | PASS | scripts/deploy_local.py and e2e_cluster.sh; passing fixture CI, real indexer completed remotely | Clean-clone full real answer still NOT VERIFIED |
| Pod persistence, >=3 endpoints, numeric HPA | PASS | Remote audit observed Chroma 646 chunks/same generation after deletion, Redis AOF marker, API replacement, three IPs and 2% numeric HPA | Full artifacts pending; live checkpoint is day3-real-audit-live-checkpoint.txt |
| Reindex without API redeploy/outage, cache invalidation/writer wait | NOT VERIFIED | Real checks use generation, request probes and lock wait log | Inspect actual artifacts |
| Wrong model => new pod 0/1/log/recovery | FAIL | Audit attempted pod logs while ContainerCreating | Wait for Running before reading conflict logs, then rerun; model guards unchanged |
| maxSurge1/maxUnavailable0/preStop/grace/visible set-image+undo | PASS | Remote real audit observed a visible UI image update and successful undo to original response hash | Preserve final artifact/source SHA scope |
| Repeated top, indexer peak/limit/margin | NOT VERIFIED | Real Job sampler and HPA measurements running; limit 1 GiB | Compute sampled peak/margin from artifact, state sampling limitation |
| Four separately broken/restored stages | NOT VERIFIED | scripts/failure_experiments.py isolates A/B/C/E collections; labels unchanged | Actual observations required in FAILURE-ANALYSIS |
| Offline lint/mypy/dependency/test/coverage>=60 | PASS | docs/evidence/day3-offline-verification.txt: API78, indexer19, evaluator8; app93.33%; Ruff/mypy/pip check pass | Rerun after material source edits |
| Strict prod manifests, all builds, Trivy HIGH/CRITICAL | PASS | CI 42289780312 and 42289773751 all required jobs successful | Final reviewed head must pass again |
| Real golden: recall drop<=0.05, citation>=0.95, all abstain | FAIL | First real audit rejected uncited high-confidence refusals; generation/gate did not pass | Canonical abstention, contradiction retry and context fixes under retest; no passing baseline invented |
| Protected main/one partner approval/passing CI | BLOCKED | Required quality strict; one approval/dismiss stale; branch protection JSON | AbdulMoez-24i-3048-SE-B must review final head; no approval invented |
| Intentional failed then fixed eval gate/disabled merge evidence | NOT VERIFIED | Isolated PR #3 changes only fixture floor; original golden/baseline preserved | Record failure, restore floor, prove pass, close unmerged |
| SonarCloud security check | BLOCKED | Code/dependency findings fixed; eight scoped private/loopback HTTP findings remain | Pending user's narrow risk-acceptance decision; no scan disabled |
| CD actually tests/publishes three main-SHA images/deploys Ingress | NOT VERIFIED | needs-gated least-privilege cd.yml implemented | Requires passing reviewed merge, then inspect actual CD and registry SHA |
| README/architecture/corpus/pipeline/four ADRs/LICENSE/AI notes | NOT VERIFIED | Core documents updated to actual source; MIT and four ADRs present | Finish measured evidence, real screenshot, seven answers and report |
| Root checker and clean checkout rehearsal | FAIL | Root checker found absent real baseline/results/failure evidence; checker unchanged | Complete substantive requirements and rerun; isolated worktree preserved |
| Classroom contents | BLOCKED | Repository link exists; no form submitted | Final passing CD URL, SHA images and committed real baseline/results required |

Local infrastructure limitation: laptop Minikube repeatedly timed out with its
2-CPU cap. A local real-model probe safely fell back after a model failure; the
following Chroma bridge failed. These are not passing real-model evidence. A
remote ephemeral real-corpus audit is running independently. A temporary local
CPU-cap change is still pending authorization; the rejected Docker socket repair
was not retried. Source files/user work were preserved.

Git workflow: original remote retained, dev fast-forwarded to all five Person 2
commits with original authorship, meaningful Day 3 milestones pushed through dev,
PR #2 open, no direct main push/reset/clean/force/init. User-author identity does
not imply handwritten code; see AI-USAGE.md.

The first real audit also observed dependency-free liveness 200, truthful readiness
503 during a >=90-second Chroma outage, unchanged API restarts and recovery. The
cache/cutover and real UI screenshot checks failed on uncited model output, so
they are not complete. Source fixes are under verification.
