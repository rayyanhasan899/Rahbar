# Day 2 execution report — 6 November 2026

## Outcome
The answer pipeline from sections 3.2 to 3.5 is implemented on branch `day2`,
based on `dev` at b41cf77. It has offline tests for every step. Nothing has been
run against the real stack yet: no real model answers, measured thresholds or
baselines are claimed in this report.

## What changed

| Area | Files |
|---|---|
| Ollama and hosted providers, shared prompt and parser | api/app/providers/llm/{ollama,hosted,prompt,base,stub}.py |
| Relevance floor, one validated retry, safe fallback | api/app/services/answer.py |
| Citation check (source, section, page) | api/app/services/citations.py |
| Injection guard for passages and questions | api/app/services/guard.py |
| Semantic cache in Redis, generation-namespaced, number guard | api/app/services/cache.py |
| Follow-ups: optional `history`, UI checkbox | api/app/schemas.py, ui/index.html |
| X-Cache header, 503 on retrieval failure | api/app/routes/ask.py |
| Metrics: retrieval and generation latency, cache, abstentions, fallbacks, retries, tokens, injection flags | api/app/routes/metrics.py |
| Retriever split into `embed` and `retrieve` so the cache reuses the vector; search logic unchanged | api/app/retrieval/{chroma,base,stub}.py |
| New settings and ConfigMap keys | api/app/config.py, k8s/base/configmap.yaml |
| CI: e2e-eval gate on fixtures, Trivy scan, PRs into dev run CI | .github/workflows/ci.yml |
| Measurement helpers | scripts/score_margins.py, scripts/cache_threshold_experiment.py, eval/cache-pairs.yaml |
| Docs | ADR 0003, PIPELINE.md Day 2 sections, REQUIREMENTS.md, TEAM-PLAN.md, AI-USAGE.md |

## Verification actually done

| Check | Result | Where |
|---|---|---|
| New service, provider, guard and cache tests | 46 passed | Run without FastAPI and Prometheus installed, using local import stand-ins; real libraries still needed |
| Day 1 evaluator tests | 8 passed | Same environment |
| mypy over api/app | No issues in 25 files | |
| ruff with CI's default rules | Clean for new code | Day 1's health.py has one 117-character line, outside CI's default rules |
| Route tests (test_ask_route.py) and Day 1 starter and readiness tests | **Not run** | Need FastAPI; run `make test` on a laptop or in CI |
| e2e-eval and Trivy jobs | **Not run** | First CI run on the pushed branch |

## Known gaps, in order of risk
1. `eval/fixtures/baseline.json` does not exist, so e2e-eval fails closed until a
   passing local run writes it (TEAM-PLAN task 4).
2. `RELEVANCE_FLOOR` 0.45 and `CACHE_THRESHOLD` 0.95 are unmeasured candidates.
   If nomic-embed-text scores the hostel question above 0.45, the fixture's
   must-abstain case fails until the floor is measured.
3. The Trivy gate fails on fixable CRITICAL findings in base images, if any.
   The scanner image `aquasec/trivy:0.58.1` is pinned by tag; pin it by digest.
4. The cluster still runs dummy data and the stub provider (TEAM-PLAN task 12).
5. Follow-ups use the previous question plus the new one as the retrieval query,
   without an LLM rewrite. Vague follow-ups may retrieve poorly; measure before
   changing.
