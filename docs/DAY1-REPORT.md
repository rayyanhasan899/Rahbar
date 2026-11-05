# Day 1 execution report — 5 November 2026

## Outcome
Implemented the Day 1 foundation in the existing repository and on dev, without
changing main or its remote. Eight selected public documents contain six PDFs
with 194 physical pages plus two HTML pages. The genuine 2023/2026 withdrawal
deadline difference is documented. Fifteen source-grounded golden questions
were committed before any tuning. Downloaded third-party documents and full
extracts remain ignored.

Implemented PDF/OCR, HTML/Markdown/text extraction, conservative cleaning,
section-aware lexical-token chunks, bounded real embeddings and staged Chroma
publication. A shared-PVC filesystem lock serializes scheduled and manual
writers. Model/dimension/generation metadata is published only after a complete
write; failure does not delete the live generation. Cache integration remains
Day 2 work. The API never ingests on startup.

## Actual verification

| Check | Observed result |
|---|---|
| Offline API tests | 13 passed; 75.14% app coverage |
| Offline indexer tests | 18 passed, including OCR path, table columns and cross-process lock |
| Offline evaluator tests | 8 passed, including gate boundaries and missing measurements |
| Dependencies | pip check passed |
| Ruff / mypy | Passing Day 1 CI lint job; final local output in day1-verification.txt |
| Strict manifests | 27 valid, zero invalid/errors/skipped; kubeconform v0.6.7 against Kubernetes 1.34 |
| Images | All three built locally and in GitHub CI, non-root Dockerfiles |
| Real fixture indexer CLI | All five stages completed; 12 real 768-dimensional chunks published |
| Real corpus experiments | Three configurations completed; results below |
| Local Kubernetes | Three API pods Ready, UI/Chroma/Redis Ready, dummy Job completed, three PVCs Bound |
| Ingress | Stub ask succeeded with matching retrieved/cited references |
| Networking | UI to API allowed; UI to Chroma blocked while DNS resolves |
| HPA | Final min3/max8, three replicas, numeric 2%/70% CPU sample |
| CI | All seven Day 1 jobs passed at run 41976761836; current checkpoint checks are on PR #1 |

| Tokens / overlap | Chunks | recall@3 | recall@5 | Stored / original lexical tokens |
|---|---:|---:|---:|---:|
| 300 / 40 | 647 | 0.846154 | 0.846154 | 1.089832 |
| 500 / 75 | 565 | 0.846154 | 0.846154 | 1.078163 |
| 700 / 100 | 536 | 0.846154 | 0.846154 | 1.061650 |

These are real retrieval measurements over 13 answerable cases, not generation
evaluation. q08/q09 missed their designated reference clauses; per-question hits
are retained. 700/100 is the provisional lower-duplication candidate. The
experiment used the initial extraction snapshot, with source/model/cache
fingerprints recorded. Explicit PDF table-row augmentation was added later and
must be retuned before final shipping. No generation baseline was invented.

## Commands and evidence

Executed repository inspection and live remote checks; created dev; configured
the supplied author email locally; committed/pushed meaningful milestones;
opened draft PR #1 naming the corpus. Ran the supplied serial corpus fetcher,
hash verification/audits, PDF extraction and OCR, visual old-page inspection,
real chunk experiments, real fixture indexing, offline tests/coverage, Ruff,
mypy, dependency checks, three Docker builds, strict rendered-manifest
validation, kubectl apply/rollout/probes, Ingress and policy connectivity tests,
metrics/HPA/endpoints sampling and the submission checker.

Reproducible entry points:

```bash
source .venv/rahbar-env.sh
python corpus/fetch.py --verify
python scripts/audit_corpus.py
# Set reachable Ollama/Chroma endpoints before this live experiment:
python scripts/chunk_experiment.py
make test
make lint
python scripts/check_submission.py
```

Important artifacts: corpus/MANIFEST.md; eval/golden.yaml;
eval/chunk-experiments.json; docs/REQUIREMENTS.md; docs/CORPUS.md;
docs/PIPELINE.md; ARCHITECTURE.md; ADRs 0001/0002; docs/AI-USAGE.md;
docs/evidence/extraction-audit.json, table-audit.json, absent-topic-audit.json,
day1-model-pin.json, day1-real-fixture-indexer.txt,
day1-real-fixture-publication.json, day1-cluster-final.txt,
day1-kubectl-top-final.txt, day1-network-final.txt,
day1-ingress-stub-smoke-final.json and day1-verification.txt.

## Debugging and preservation
Preserved the pre-existing Makefile/path-quoting/resource overrides and pinned
coverage dependency changes in their own setup commit. The original diff is
backed up in ignored .venv. All new commits use Rayyan Hassan and the supplied
rayyanhassan899@gmail.com; no partner identity or approval was invented.

Chroma initially failed because Kubernetes service links injected a TCP URL in
CHROMA_PORT, which Chroma interprets as a numeric port. Disabling service-link
injection in its StatefulSet fixed it; the original panic log is retained.
Cold-start load, repeated dependency-client creation and aggressive CPU-based
scaling caused local instability. Readiness now uses bounded lightweight HTTP
checks with a reused client; liveness is independent of its worker pool. The
API request was adjusted to 200m based on startup samples. A temporary HPA
diagnostic cap was restored to the required 3–8 before final evidence.
Initial failed network/cluster samples remain distinct from the final passing
samples. Resource limits still need real generation/indexer-peak measurements.

WSL could not directly use the Windows-only Chroma port-forward. A temporary
project-local loopback/stdin bridge enabled the real experiment without copying
kubeconfig keys or modifying firewall rules. The authorized Ollama listener
change made the existing model accessible from WSL. Its weights remain on D:.
The local WSL Minikube wrapper's environment propagation was also corrected;
it now locates the existing D: profile. No cluster recreation or data wipe.

The first CI attempt caught a real mypy narrowing error; the fix was pushed and
all seven jobs subsequently passed. Dummy fixture-bootstrap is not labelled
as a real semantic-retrieval/generation quality gate.

## Git and external state
Repository: https://github.com/rayyanhasan899/Rahbar
Draft PR: https://github.com/rayyanhasan899/Rahbar/pull/1
Verified Day 1 CI: https://github.com/rayyanhasan899/Rahbar/actions/runs/41976761836
Work is on dev; main remains at the initial commit. No merge or direct main
push was performed. Branch settings and GitHub Secrets were not changed.

## Remaining work and genuine user actions
This is not submission-ready. Day 2 must complete a real constrained provider,
grounding/citation/retry/fallback/abstention/injection defenses, conversation and
semantic cache behavior, measured thresholds, extended metrics, real-corpus
generation evaluation/baseline, Trivy and real fixture e2e gating. Supply the
real corpus to the cluster, configure tested model egress, retune the enhanced
extractor and replace dummy configuration in both batch templates. Weekly
reindex stays suspended until then. Day 3 still needs full resilience/rollback/
pin-conflict/four-stage failures, remaining docs/ADRs, registry publication,
successful CD, clean-clone rehearsal and final submission audit.

Before merge, the real partner must review/approve and contribute under their
own identity. Required branch checks/one-review settings need the specified
account-level approval when ready. Before CD, configure Docker Hub credentials
through secure GitHub settings or CLI input; never paste credentials into chat.
No new package installation is required from the user to start Day 2 locally.
The submission checker still reports expected Day 2/3 failures; they are not
suppressed and no failed requirement is presented as a pass.
