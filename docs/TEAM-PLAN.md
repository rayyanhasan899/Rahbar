# Two-person plan: 6 to 8 November 2026

Deadline: **Sunday 8 November, 23:59 PKT**. Person 1 is Rayyan (did Day 1, owns the
repository and the laptop with minikube, Ollama and the real corpus). Person 2 is
Moez (Day 2 code on branch `day2`). Each person commits under their own identity
and reviews the other's pull request, which covers the one-approval rule.

## Where things stand (Friday evening)

| Area | State |
|---|---|
| Indexer, corpus, Chroma, K8s skeleton, CI lint/test/build | Done on `dev` (Day 1 report) |
| Answer pipeline, providers, cache, injection guard, follow-ups, metrics | Code and offline tests on `day2` |
| e2e-eval and Trivy CI jobs | Written on `day2`, not yet run |
| Real-stack measurements (floor, cache threshold, baseline) | Not started |
| Cluster on real corpus and real model | Not started (still dummy) |
| CD, failure analysis, engineering notes, final docs | Not started |

## Friday night: land Day 2

| # | Task | Who | Done when |
|---|---|---|---|
| 1 | Push `day2`, open PR `day2` into `dev` | Moez | PR open, CI running |
| 2 | `make install && make test && make lint` on a laptop | Moez | All API tests pass, including test_ask_route.py, which only runs with FastAPI |
| 3 | Review the PR (code, ADR 0003, tests) and approve or request changes | Rayyan | Review recorded on GitHub |
| 4 | Fixture baseline: local Chroma + Redis + Ollama, index `eval/fixtures`, API with `RETRIEVER=chroma LLM_PROVIDER=stub`, run the fixture golden set with `--baseline eval/fixtures/baseline.json --update-baseline` | Moez | `eval/fixtures/baseline.json` committed, e2e-eval green |
| 5 | Fix any Trivy CRITICAL findings (usually a base-image bump) | Moez | build job green |

Commands for task 4 are in the e2e-eval job in `.github/workflows/ci.yml`; run the
same steps locally with `CHROMA_PORT=8001`. If the hostel question is not declined,
run `python scripts/score_margins.py /tmp/fixture-results.json` and adjust
`RELEVANCE_FLOOR` before writing the baseline.

## Saturday 7 November: measure, switch the cluster, Day 3 work

Morning (needs Ollama and the real corpus):

| # | Task | Who | Output |
|---|---|---|---|
| 6 | Retune chunking after Day 1's table-row change: rerun `scripts/chunk_experiment.py` for three settings | Rayyan | Updated table in PIPELINE.md and ADR 0002 |
| 7 | Real eval: index real corpus, API with `LLM_PROVIDER=ollama-host`, run `eval/golden.yaml` | Rayyan | `eval/results.json` |
| 8 | Set the floor: `scripts/score_margins.py eval/results.json`; read every answer against `expect` | Moez (with 7's file) | Floor row in PIPELINE.md, ConfigMap value |
| 9 | Cache threshold: `scripts/cache_threshold_experiment.py` | Moez | Threshold table and the false hit in PIPELINE.md |
| 10 | Temperature 0.0 vs 0.2 on the golden set | Moez | One line in ADR 0003 |
| 11 | Write `eval/baseline.json` with `--update-baseline` after 8 to 10 | Rayyan | Committed baseline and results |

Afternoon:

| # | Task | Who | Output |
|---|---|---|---|
| 12 | Cluster on real data: corpus volume for the indexer Job, remove `--dummy`, ConfigMap `RETRIEVER=chroma`, `LLM_PROVIDER=ollama-host`, `EMBED_MODEL=nomic-embed-text`, NetworkPolicy egress from api to the host's Ollama, resume the weekly CronJob | Rayyan | Grounded answer through Ingress, saved under docs/evidence |
| 13 | Cluster demos: X-Cache MISS then HIT, reindex then MISS, poisoned-chunk question, pin conflict (change EMBED_MODEL only, API stays unready), Chroma pod deletion keeps data, rolling update and rollback | Rayyan | Evidence files and screenshots |
| 14 | CD workflow: on `main`, needs CI, build and push SHA-tagged images to Docker Hub, deploy to an ephemeral kind cluster and smoke-test; Docker Hub token stored as a GitHub secret by the repo owner | Moez writes, Rayyan adds secrets | Successful CD run link |
| 15 | Branch protection on `main`: required checks and one approval | Rayyan (owner) | Settings screenshot |
| 16 | Measure indexer peak memory and API usage under the eval run; set requests and limits | Rayyan | Updated manifests, `kubectl top` evidence |

Evening:

| # | Task | Who | Output |
|---|---|---|---|
| 17 | Failure analysis: break four of the six stages one at a time, diagnose, restore | Both, two stages each | docs/FAILURE-ANALYSIS.md |
| 18 | Engineering notes: seven answers with file and line references | Each answers about the parts they built; Moez drafts 3, 5, 6 | docs/ENGINEERING-NOTES.md |
| 19 | ADR 0004 (CD and image publishing) | Moez | docs/adr/0004-*.md |

## Sunday 8 November: finish and submit

| # | Task | Who | By |
|---|---|---|---|
| 20 | README: problem statement, CI badge, architecture diagram, apply order, clean clone to answered question, endpoint table, screenshot; LICENSE | Moez | 14:00 |
| 21 | AI-USAGE: every tool, what it wrote, what each person changed | Both | 14:00 |
| 22 | Clean-clone rehearsal on a fresh folder, following only the README | Moez (not the person who wrote the steps) | 17:00 |
| 23 | `make check`, history secret scan, final requirement-by-requirement audit | Both | 19:00 |
| 24 | Merge `dev` into `main` through the reviewed PR, confirm CD, submit links | Rayyan | 21:00, leaving buffer |

## Rules for both

- Work on branches and merge through pull requests; nobody pushes to `main`.
- A number goes into the docs only after it was measured; write "pending" otherwise.
- Never paste keys or tokens into a chat or a file. Secrets go through
  `make secret` or GitHub's secret settings.
- If one task is blocked, move on to the next independent one and note the blocker
  in the PR.
