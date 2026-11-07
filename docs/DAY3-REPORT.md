# Day 3 execution report

7 November 2026, Asia/Karachi. Deadline: 8 November 2026, 23:59 PKT.
The reviewed release has shipped: PR #2 merged as f6c702b and CD run
42341465116 passed. The complete per-requirement record is REQUIREMENTS.md.

## Outcome and remaining release dependency

| Area | Status | Actual result |
|---|---|---|
| Application and ingestion | PASS | Real public corpus, generation, historical retrieval, safe refusal, cache and injection checks |
| Kubernetes runtime acceptance | PASS | All eleven corrected checks at source 4917e45 in run 42308165966 |
| Real golden regression gate | PASS | recall@5 11/13=84.6154%; citation validity100%; both must-abstain refused; recall drop0 |
| Offline quality | PASS | API80, indexer19, evaluator8; app coverage93.39%; Ruff/mypy/pip check |
| Strict manifests | PASS |28 production resources valid,0 invalid/errors/skipped |
| Pipeline ablations | PASS | Actual A/B/C/E failures and restored reference, including separate two-clause C diagnostic |
| Root checker | PASS |162 passed,5 warnings,0 failures; checker unchanged |
| Three builds/scans | PASS at 4917e45 | All three passed the fixableHIGH/CRITICAL scan gate; UI EOL warning found in detailed review |
| Supported final UI base | PASS for build/scan/fixture | Updated in14b2333 to digest-pinned nginx1.30.6/Alpine3.24; full real audit still running |
| SonarCloud | PASS | Security/reliability/maintainabilityA after scoped owner-approved decisions and correct raw-evidence labelling |
| Genuine partner approval | PASS | AbdulMoez-24i-3048-SE-B approved PR #2 at 1a39dac on 7 November |
| Main merge, successful CD and Hub SHA images | PASS | Merged as f6c702b; [CD run 42341465116](https://github.com/rayyanhasan899/Rahbar/actions/runs/42341465116) passed; api/indexer/ui images tagged f6c702b on Docker Hub |
| Classroom submission | NOT VERIFIED | Not submitted; user did not request form submission |

The final measured run answered eight of fifteen questions with citations.
Other non-mandatory questions safely declined/fell back. Citation membership is
not semantic entailment, and the small golden set does not prove universal
correctness. Those limitations are disclosed rather than hidden by the gate.

## Repository and preserved work

Repository: https://github.com/rayyanhasan899/Rahbar
Submission PR: https://github.com/rayyanhasan899/Rahbar/pull/2
Main at this checkpoint: ce56e18db9f540293b46a636f6a3d53ccbacec7c.
All work flows through dev. Original remote and Person 2's five commits/authorship
were preserved by a safe fast-forward; main was merged into dev normally for
strict up-to-date protection. No init/reset/clean/force/direct-main push occurred.

Meaningful Day3 milestones include 9baff02(cache correctness), d8c2c98(release
workflow), b18b255(runtime/dependency patches), 8f0353f(citations/startup),
a943698(bootstrap order), 300eb83/da2121c/3dfbea9(real verification/security),
b1affb1(audit isolation), b9b0fa5(reproducible docs), 54f37ff(real-model refusal
repair), 4917e45(genuine baseline/corrected acceptance) and14b2333(supported UI
base and evidence). The final report commit and latest checks must be verified
from GitHub before merging. Git author Rayyan Hassan uses the requested email;
AI-USAGE.md discloses actual agent work and preserves Person 2 attribution.

Main protection: strict required quality check, one approving review, stale
review dismissal, administrator enforcement, conversation resolution, no force
push/deletion. Evidence: day3-branch-protection.json. No partner approval is
invented. The owner explicitly approved these settings.

## Actual commands and results

Commands ran from the existing project root unless a directory change is shown.
WSL used the inspected existing Python3.12 environment via
`source .venv/rahbar-env.sh`; no system Python replacement was performed.

| Command | Observed result |
|---|---|
| git status/branch/remote/log, fetch origin --prune, merge --ff-only origin/dev | Existing clean repo inspected; all five Person 2 commits preserved; original remote retained |
| corpus/fetch.py --verify; fresh image audit in CI | All8selected file hashes matched;6PDFs/194physical pages; OCR limitations retained |
| ruff check api indexer eval corpus scripts | Passed |
| cd api && mypy app |25source files, no issues |
| cd indexer && mypy pipeline |11source files, no issues |
| cd api && pytest -q --cov=app --cov-fail-under=60 |80 passed;93.39%app coverage |
| cd indexer && pytest -q |19 passed |
| pytest -q eval/tests |8 passed |
| python -m pip check |No broken requirements |
| kubectl kustomize k8s/overlays/prod with kubeconform -strict -summary -kubernetes-version 1.34.0 |28valid,0 invalid,0 errors,0 skipped |
| Three docker build jobs using exact github.sha/VCS_REF |All succeeded at 4917e45; new UI base rebuild pending at 14b2333 |
| Pinned Trivy image --scanners vuln --ignore-unfixed --severity HIGH,CRITICAL --exit-code 1 |All3 gates passed; raw scan logs retained; this excludes unfixed/lower severity findings |
| bash scripts/e2e_cluster.sh in a clean kind/Calico cluster |Real fixtures indexed before API readiness; Ingress fixture gate passed |
| Same bootstrap with CORPUS_MODE=real and real_cluster_checks.py |Corrected source 4917e45: all 11checks passed |
| eval/run_eval.py through Ingress against original golden and preserved baseline |Real final recall.846154, citation1.0, abstention1.0, drop0 |
| scripts/chunk_experiment.py |738/671/646 chunks at 300/40,500/75,700/100; all recall.846154 |
| scripts/cache_threshold_experiment.py |113real comparisons; .75lowest tested zero guarded false hits,4/5paraphrase hits |
| scripts/failure_experiments.py |OCR0->recovered8 pages; flat chunks recall.230769->.846154; two-clause top1.5->top5 1.0; version mixing removed |
| python scripts/check_submission.py |Current root162pass/5warn/0fail |
| Isolated worktree pytest/import probe and clean remote checkout/install/deploy |Tests loaded isolated source; clean remote bootstrap served real corpus |

The coverage tooling is pinned: pytest-cov7.1.0 and coverage7.17.2 in the complete
wheel-hash lock. Unit tests use fakes/mock transports and never call external
services/models. CI installs hash-locked binary wheels, pins Actions to full
SHAs, validates production manifests and gates publishing/deployment with needs.

## Evidence and substantive observations

Primary runtime evidence is docs/evidence/day3-audit-4917e45/report.json with its
associated network, dependency-probe, persistence, model-pin, resource, rollout,
reindex and poisoned-index artifacts. Its original/restored UI HTML hashes match,
and the corrected check requires HTTP200. Its real-ui.png is a real browser
capture of the app and cited Ollama answer, not an illustration or mockup.

Reindex produced a new publication generation at the same646 chunks. All47question
probes returned200 while the API template stayed unchanged. A MISS crossed
publication and subsequent requests HIT. A manually triggered Job entered the
same lock only after waiting208.441 seconds. The indexer was never granted Redis
access. Redis AOF and Chroma index/count survived pod deletion; three API endpoint
IPs and numeric HPA metrics were observed. A wrong-model new pod stayed unready,
logged the exact mismatch, and recovered after configuration restoration.

Memory: earlier real Job 64 samples peaked at 203 MiB; final Job 66 samples at 160 MiB.
Limit 1024 MiB gives minimum observed margin 821 MiB across these runs. These are
sampled maxima, not proof that no shorter peak occurred. HPA/metrics details and
all seven engineering answers with file/line references are in ENGINEERING-NOTES.

The genuine baseline was explicitly established in source 54f37ff only after
absolute gates passed. It was preserved for source 4917e45, not silently updated.
Provenance is eval/BASELINE.md; committed files are eval/baseline.json and
results.json. Fresh chunk/cache inputs include original golden/source hashes,
model digest/dimension and extraction engine/lock fingerprints. Downloaded PDFs
and full extraction caches remain ignored and uncommitted.

Gate proof: controlled PR #3 changed only the owned-fixture floor .65->.45 at
abea020. Run42291331805 failed an answered must-abstain case and failed quality;
its merge button was disabled. Restoring .65 at 6698f78 produced passing
run 42293007228 without relabelling questions/baseline. Paired screenshots/results
are day3-eval-gate-{failed,fixed}.*. PR #3 was closed without merging or deleting
its branch; no review or merge approval was fabricated.

Historical failures are retained, including the uncited confident-refusal output,
the real 3888.2-second build ending in a wheel hash mismatch, admission startup
races, and a502page that exposed a weak rollback assertion. That502response was
renamed as raw .html.txt evidence with unchanged bytes, not edited into a success.
The checker itself was never edited to obtain a green result.

## Checker warnings

1. The only secret-shaped history file is the excluded placeholder template,
   not a real credential.
2. Commit-count imbalance is factual; it is not a fabricated contribution split.
   Person 2's original commits remain intact. Review/human contribution must be real.
3. The checker misses the REST collection-count predicate; real readiness/outage
   tests prove nonempty checks and dependency failure behavior.
4. The checker misses the composed cache eligibility conditions; tests cover
   declined answers/follow-ups/injections and per-entry expiry.
5. The checker misses the structured Job restartPolicy; strict validation and
   actual Job/CronJob manifests contain OnFailure and were executed.

Warnings are explained by implementation/evidence rather than deleting checks or
adding code-shaped comments to fool its patterns.

## Laptop and authorized settings

The existing laptop has about 7.7 GiB RAM; the Minikube node has4 GiB. Docker was
rechecked running. C: had roughly5 GiB free at initial Day3 inspection, D: ample
space. The two-CPU control plane timed out under load. The owner approved a
temporary four-CPU allowance, with restoration required after verification.
An ignored project-local kubectl wrapper makes Python subprocesses use the same
existing Windows cluster context as the WSL shell; Linux kubectl had otherwise
looked at unconfigured localhost:8080. No account/global kubeconfig was replaced.

Normal Minikube image loading stalled; native Docker delivery loaded the three
tested 54f37ff images without recreating the node. The verified corpus transfer
and real Job completed in 6m46s and published **646 chunks**, matching the remote
content fingerprint and 768-dimensional pin. All three new API pods are ready;
/healthz and /readyz return 200. The original two-CPU allowance is restored and
was verified with the pods still ready. Evidence: docs/evidence/day3-local.

The laptop model's Ingress requests returned safe low-confidence refusals/fallbacks,
not cited answers. Host logs identify the concrete blocker: Ollama could not
allocate its 939,524,096-byte KV-cache buffer for the 8192 context and returned
HTTP500. This is a host model memory allocation failure, not an observed
Kubernetes OOMKilled/137. The working index/readiness and safe fallback are not
presented as a passing local generation gate. Larger-memory remote clusters
supply the passing real-generation evidence. No system RAM/pagefile setting or
rejected Docker socket repair was changed.

A development-only localhost Ingress alias and loopback port-forward make the
actual laptop UI available at http://localhost:18080 without editing hosts files.
The production manifest retains rahbar.local. The local image is explicitly the
pre-merge 54f37ff verification image, not a main release SHA. No secret values were
read or written to Git.

SonarCloud: the owner approved exactly eight private/loopback HTTP findings and
signed in personally. Their accepted-risk comments explain the destinations,
public data and residual transport risk; they reopen 10November2026. Other issues,
scanning, policies and required approval remain enabled. Current quality ratings
areA; the final source reanalysis must also pass.

## Exact remaining actions and submission contents

1. Inspect the supported-UI full real audit42326871487. Builds, scans and fixture
   deployment passed; the laptop bootstrap and CPU restoration are complete.
   Local real generation remains memory-blocked; no larger-memory result is
   substituted as a laptop result.
2. Finish the final reviewable documentation/evidence commit; require passing
   checks on that head. Person 2 (AbdulMoez-24i-3048-SE-B) must genuinely review and
   approve PR #2. Rayyan/Codex cannot supply that approval.
3. Merge only that passing reviewed PR through GitHub. Then verify cd.yml on the
   actual merged main SHA: reusableCI, three Hub publications, registry pull/load,
   fixture indexing, rollout and smoke through Ingress. Inspect deployed revision
   and image references. Do not use a pre-merge SHA as release proof.
4. Put these four exact items in the team's one Classroom entry: repository URL;
   direct successful cd.yml run URL; three Docker Hub image links showing that
   main SHA tag; committed eval/results.json and eval/baseline.json. Their final
   release URLs are NOT VERIFIED until step3 actually succeeds. No form is submitted
   by this task.

The next engineering work is release verification and genuine review, not another
implementation plan. If approval or publishing credentials block release, report
BLOCKED with the exact failed run/action; do not weaken protection or fabricate
external evidence.

## Evidence-file and checker scope

The checker output quotes its own starter-marker literal. Storing that raw output
as .txt caused the unchanged checker to report the quote as unfinished source.
The raw bytes are now preserved as day3-submission-checker.out; no substantive
requirement or checker logic was changed. Native root verification had already
passed; the WSL clean-checkout run is repeated against the final committed tree.
Generated evidence is not application source. Historical502bytes are likewise
retained explicitly as raw HTTP evidence rather than modified into valid UI HTML.
