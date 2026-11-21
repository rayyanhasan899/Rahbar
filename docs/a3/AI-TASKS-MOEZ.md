# AI tasks for Moez: Parts B, C, E and the release side of F

Give this file and `docs/a3/PLAN.md` to the AI assistant. Branch `dev2`, one commit per
working feature, author AbdulMoez-24i-3048-SE-B. The contracts in PLAN.md are fixed.

Rules: no invented numbers; Python 3.12, ruff line length 100; plain
`print("label", value)` output; every script a Job runs takes URLs and paths from flags
or environment variables and exits non-zero on failure; unit tests with fakes under
`eval/tests/`.

## B0. Golden set

- `eval/golden.jsonl`, one object per line: `id`, `question`, `origin`
  (`human|synthetic`), `reviewed`, `kind` (`answerable|unanswerable|hard`),
  `hard_reason`, `relevant [{source, page, section}]`, `expect`.
- `eval/convert_golden.py`: the 15 Assignment 2 questions from `eval/golden.yaml` into
  that format, keeping their ids. Page candidates come from the chunks that the stored
  run (`eval/results.json`) retrieved for the same source and section; a person confirms
  the physical page. q10 (2023 rules) becomes `unanswerable` once Part A archives old
  versions.
- `eval/golden_check.py`: at least 25 questions, 15 answerable with source and page,
  5 unanswerable, 5 hard, 8 human, 8 synthetic and reviewed; exit 1 otherwise.
- `eval/synth_questions.py`: samples chunks from the active collection, asks the model
  for one question per chunk, writes `eval/synthetic-candidates.jsonl` with
  `reviewed: false` and the chunk's source, page and section.

## B1. Module level (embedding)

`eval/embedding-pairs.jsonl` (15+ paraphrase pairs, 15+ unrelated pairs, domain
sentences). Mean cosine per group and the gap; embedding time per chunk over real chunks
from Chroma; determinism (same text twice, largest absolute difference). Same model and
prefix as the indexer.

## B2. Component level (retrieval)

recall@3, recall@5, MRR, nDCG@5 over answerable and hard questions, from the ranked
`retrieved` list. A retrieved chunk is relevant when its source matches and its page or
section matches a `relevant` entry. Noise: `--typos` (seeded character edits) in the
suite; noise documents are ingested by hand, then the suite runs with a label.

## B3. End-to-end level (answers)

- Faithfulness: an LLM judge sees the retrieved chunk texts (read from Chroma by id) and
  the answer, returns `supported|partial|unsupported`; score 1, 0.5, 0. Only answered
  questions are judged. Judge prompt in `eval/judge_prompt.txt`, temperature 0, seed.
- Abstention correctness on unanswerable questions; false abstentions on answerable ones.
- Citation validity (the Assignment 2 definition).
- Latency p50 and p95 from the client; `X-Cache` per row (cache hits are reported, and a
  run with hits is marked, because they distort latency and stochasticity).
- `eval/hand_labels.jsonl` and an agreement report (rate and confusion counts).

## B4. One command

`eval/suite.py --label <name>` runs B1 to B3 with a fixed seed and writes
`eval/results/suite-<UTC timestamp>-<label>.json` and `.md` (summary table of all three
levels), and `latest-<label>.json`. `eval/suite.py --compare A.json B.json` prints the
difference per metric. API seed: a `SEED` setting passed to Ollama `options.seed`.

## C. Change experiment and release gate

- `eval/gate.yaml` (local) and ConfigMap `rahbar-gate` (cluster) with the same keys:
  `max_recall5_drop`, `min_faithfulness`, `max_p95_latency_seconds`,
  `abstention_not_below_baseline`, `min_citation_validity`. Values chosen by a person.
- `eval/gate.py --baseline --candidate --thresholds`: one line per rule, exit 0 or 1.
- Candidate ConfigMap `k8s/candidate/configmap.yaml` (collection `rahbar-cand`, changed
  chunking chosen by a person).

## E. Drift and coverage

- `eval/coverage.py --live eval/live_queries.jsonl --golden eval/golden.jsonl
  --threshold T --min-share S`: nearest golden question per live query, share at or above
  T, uncovered queries grouped into topics, result file in `eval/results/`, exit 1 when
  the share is below S. T and S are required flags (a person chooses and justifies them).
- E1 queries and E4 questions are written by people (manual file).

## F. Release side

- `eval/Dockerfile` (built from the repository root, reuses the indexer's hashed lock,
  so no new dependency lock is needed), `make images` builds `rahbar-eval`.
- `k8s/eval-job.yaml`: runs the suite then the gate against `http://api:8000`, results on
  the `eval-results` PVC, thresholds from `rahbar-gate`, `backoffLimit: 0`, fails when
  the gate fails. `k8s/eval/`: the PVC, the gate ConfigMap, a results shell Pod.
- NetworkPolicies: eval pods reach the API, Chroma and Ollama; the API and the
  candidate API accept them.
- `k8s/candidate/`: `api-candidate` Deployment and Service, `eval-job-candidate.yaml`.
- `scripts/release.sh`: candidate eval Job, then either stop (gate failed) or
  `kubectl set env deployment/api CHROMA_COLLECTION=...` with a change-cause annotation
  and `kubectl rollout status`; `--force` releases a known-bad candidate for the undo demo.
- F5: requests and limits from measured `kubectl top` values (manual measurement).
