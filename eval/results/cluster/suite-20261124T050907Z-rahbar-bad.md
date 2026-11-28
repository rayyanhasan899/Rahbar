# Suite rahbar-bad (20261124T050907Z)

Golden set: /app/eval/golden.jsonl (31 questions), seed 42, API http://api-candidate:8000, collection rahbar-bad.

| Level | Metric | Value |
|---|---|---|
| module (embedding) | paraphrase mean cosine | 0.8239 |
| module (embedding) | unrelated mean cosine | 0.5545 |
| module (embedding) | gap | 0.2694 |
| module (embedding) | ms per chunk (mean) | 18.4738 |
| module (embedding) | determinism max abs difference | 0.0000 |
| component (retrieval) | recall_at_3 | 0.7885 |
| component (retrieval) | recall_at_5 | 0.9231 |
| component (retrieval) | mrr | 0.7641 |
| component (retrieval) | ndcg_at_5 | 0.7973 |
| end-to-end | faithfulness | 0.3571 |
| end-to-end | judged_answers | 14 |
| end-to-end | abstention_correctness | 1.0000 |
| end-to-end | false_abstention_rate | 0.4615 |
| end-to-end | citation_validity | 1.0000 |
| end-to-end | latency_p50_seconds | 2.0220 |
| end-to-end | latency_p95_seconds | 4.3540 |
| end-to-end | cache_hits | 0 |
