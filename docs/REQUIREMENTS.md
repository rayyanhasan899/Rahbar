# Day 3 requirement traceability

Verification date: 7 November 2026, Asia/Karachi. Deadline: 8 November 2026,
23:59 PKT. The assignment PDF controls requirements. PASS refers to observed
behavior, FAIL to an unsuccessful observation, BLOCKED to an external dependency,
and NOT VERIFIED to absent required evidence. Historical failures are retained.

The corrected full real-corpus audit passed at source 4917e45 in
[run 42308165966](https://github.com/rayyanhasan899/Rahbar/actions/runs/42308165966).
Its eleven checks are all PASS. Evidence root: docs/evidence/day3-audit-4917e45.
Code/manifests/workflows are unchanged since that source; subsequent edits are
reports, evidence and a corrected physical-page comment in a diagnostic YAML.

| Requirement | Status | Implementation, verification and evidence | Remaining dependency |
|---|---|---|---|
| Public corpus >=6 documents, >=40 pages, seven properties | PASS | Eight selected documents, six PDFs/194 pages; CORPUS.md, MANIFEST, version/table/extraction audits | OCR/table limitations disclosed |
| URLs, source hashes, versions/supersession, polite serial fetch; no PDF commit | PASS | Live remote re-fetch and 8/8 pinned hashes, source inventory and tracked-file exclusion | None |
| Changed version pair, image-only PDF, informative table, long definitions, exact and absent topics | PASS | 2023/2026 clause4.25, eight scanned startup-policy pages, grade-point/fee tables, AI definitions, original golden | No invented source availability |
| Golden 8ordinary/2version/2exact/2abstain/1injection before tuning | PASS | Original d7b5e88 labels unchanged; golden SHA in experiments/provenance | Additional failure diagnostic kept separate |
| Five indexing stages, PDF/OCR, HTML/text, aligned Markdown fixture headings | PASS | Real image ingestion completed; 19 offline tests; fresh image-matched extraction profile | Six empty pages disclosed |
| Structure-aware lexical-token chunking/overlap/metadata | PASS | Source, section, starting physical page, version, superseded and stable IDs; tests and real queries | Lexical tokens differ from model tokens |
| Three real chunk configurations/storage amplification | PASS | 300/40:738 chunks/1.061133; 500/75:671/1.047257; 700/100:646/1.029494; each recall5=11/13 | 700/100 chosen at equal recall |
| Same model/dimension, cosine, Chroma client/server1.0.12 | PASS | nomic768, recorded digest, collection/pointer pins and query prefixes | Model tags alone are not immutable bytes |
| Safe repeat indexing, staged publication, serialized manual/weekly writers | PASS | Same646 chunks/newgeneration; manual writer waited208.441s; writer/reindex logs | Old generations retained intentionally |
| No API-startup ingestion and generation invalidation without indexer Redis | PASS | Read-only startup check; unchanged API template through cutover; MISS then HIT; policies unchanged | None |
| Current and explicitly historical retrieval; turns | PASS | Version predicate tests, q09/q10 real answers, cited real follow-up in resources.json | Benchmark misses remain honest |
| Shared semantic cache, exclusions, expiry and measured threshold | PASS | 113 real pairs, guarded falsehits3/1/0 at .65/.70/.75; .75 selected; entryTTL/intent tests | Small calibration set is not universal proof |
| Schema/retry/fallback/relevance/grounding/citations/abstention | PASS | 80 API tests; canonical refusals; real golden validity100%, both absent topics refused | Five non-mandatory final questions declined/fell back |
| Injection defense with actually indexed poisoned chunk | PASS | poison-probe.json records stored poison ID and real model refusal/fallback, no planted claim obeyed | Does not prove useful answer to every poisoned question |
| Pluggable provider and deliberate low temperature | PASS | Real Ollama3B at 0.2; optional HTTPS hosted adapter mocked; timeout/context safety | Hosted mode not independently live-tested |
| Request/JSON logging, metrics, cache/retry/abstention/tokens | PASS | Runtime metrics.txt, JSON indexer/provider logs and tests | Logs do not establish semantic entailment |
| Namespace, APIx3/UI, Chroma STS volumeClaimTemplates, RedisPVC | PASS | final-resources.json; persistence tests and actual three endpoints | None |
| Four ClusterIP Services, / and /api Ingress, ConfigMap/Secret placeholder | PASS | Real network/Ingress200 and manifests; placeholder excluded, no actual secret values read | None |
| OnFailure/backoff indexer Job; same weekly CronJob | PASS | Initial/reindex Jobs completed, weekly template image/args and shared lock | Weekly PVC snapshot is curated, not an automatic web crawler |
| Dedicated SAs, tokenoff/nonroot/readonly/dropcap/resources | PASS | workload-security-summary.json checks every actual workload and init container | Writable mounts limited to required paths |
| API startup/liveness/readiness, truthful dependency outage | PASS | >=90s Chroma outage: health200/ready503, unchanged restarts/UIDs, recovered | Swapped probes discussed causally, not falsely claimed deployed |
| Enforced network allow paths, DNS/provider, UI->Chroma denied | PASS | network.json: correct service DNS; UI wget timed out to Chroma; all allowed paths connected | Backend/private-model HTTP accepted only in reviewed scope |
| Correct initial dependency/index/API bootstrap | PASS | Clean remote checkout/images, verified PVC transfer, completed index then API rollout | Separate local laptop state below |
| Pod deletion/persistence, >=3 endpoint IPs, numeric HPA | PASS | Chroma generation/count, Redis AOF marker and API replacement; resources.json | No invented scale-out |
| Reindex without API rollout/outage, cache invalidation/serialization | PASS | 47 successfulHTTP200 probes, unchanged deploymenttemplate, newgeneration and writer wait | None |
| Changed embedding model => new0/1, explicit logs, restored recovery | PASS | pin-conflict.json with deliberatewrongmodel and recovered646chunk publication | None |
| maxSurge1/maxUnavailable0/preStop/grace, visible image set/undo | PASS | Corrected check requires HTTP200 and exact original hash; original/demo/restored HTML | Earlier502 false-positive retained as negative evidence |
| Repeated top, indexer memory/limit/margin | PASS | Earlier64 samples peak203Mi; final66 samples peak160Mi; limit 1024Mi, minimum observed margin 821Mi | Sampling may miss brief peak |
| Four separately broken and restored stages | PASS | A eightpages0chars->OCR; B recall84.62->23.08->84.62; C two-clause50->100%; E mixed versions->validfilter | Original golden top1/unfiltered recall unchanged, disclosed |
| Offline lint/types/dependency/tests/coverage>=60 | PASS | API80/93.39%, indexer19, evaluator8; Ruff/mypy/pip check, source-isolated tests | Final report notes verification revision |
| Strict production manifests, all 3image builds/Trivy gates | PASS | All28strictvalid; fullCI42308165966 success, fixableHIGH/CRITICAL gate | Scan intentionally uses --ignore-unfixed, not a claim of zero total CVEs |
| Real golden baseline/results and regression gate | PASS | Genuine54f37ffbaseline preserved; final4917e45recall.846154/drop0, validity1, abstain1 | Eight of 15 final responses cited; other safe refusals disclosed |
| Actual failed-then-fixed evaluation gate evidence | PASS | PR #3 abea020/run 42291331805 failedmust-abstain; 6698f78/run 42293007228 passed; paired screenshots/results; closedunmerged | Separate Sonar finding on demoPR not hidden |
| Protected main with one genuine partner approval | PASS | Strict quality +oneapproval/dismissstale/adminenforced; protectionJSON; AbdulMoez-24i-3048-SE-B approved PR #2 at 1a39dac on 7Nov | None |
| SonarCloud check | PASS | Eight owner-approved private/loopbackHTTP findings accepted until10Nov; securityA | Actual reanalysis passed A ratings after raw502artifact was labelled .html.txt; scan remains on |
| Reviewed merge and actual main-SHA CD/Hub release | PASS | PR #2 merged as f6c702b with 25 checks passing; [CD run 42341465116](https://github.com/rayyanhasan899/Rahbar/actions/runs/42341465116) passed test, build-push and deploy; three f6c702b-tagged Docker Hub images | None |
| README, architecture, corpus/pipeline/failure/seven answers/fourADRs/AI/LICENSE | PASS | Actual screenshot and measurements, code/line refs, accurate human/AI disclosure | Release links recorded after CD run 42341465116 |
| Root submission checker | PASS | Current root:162pass/5 warnings/0fail; checker unchanged | Rerun final checkpoint; warnings explained in Day3report |
| Clean checkout rehearsal | PASS | Isolated source imports/tests; real audit uses clean GitHub checkout +hashlockedinstall and actual deployment | No stale working-directory cache dependency claimed |
| Classroom contents | NOT VERIFIED | Repo, [CD run 42341465116](https://github.com/rayyanhasan899/Rahbar/actions/runs/42341465116), three f6c702b Docker Hub tag links and committed results/baseline are ready | Form not yet submitted |

Local laptop: its real Job completed in6m46s, published646chunks and the same
content fingerprint as the remote audit. All three API pods passed health and
readiness. The approved temporary CPU increase was restored to two and verified.
Local model generation is BLOCKED by an observed896MiB Ollama KV-cache allocation
failure; safe fallback was observed. The successful larger-memory remote gate
is not presented as a laptop result. A development-only localhost Ingress alias
serves the UI through a loopback forward without changing the hosts file. The
prior rejected Docker socket repair was not retried; no global RAM settings changed.

Git: original remote retained; dev safely fast-forwarded to all five Person 2
commits with original authorship, meaningful Day3 milestones pushed via dev/PR #2.
No reset/clean/init/force/directmain push or invented partner approval.

Supported UI14b2333 builds, all three scans, fixture deployment and all eleven
checks in real audit42326871487 passed. SonarCloud reanalysis passes with A ratings. The
raw checker output is preserved as .out, so its quoted marker is not mistaken
for an unfinished source stub; the checker itself remains unchanged.
