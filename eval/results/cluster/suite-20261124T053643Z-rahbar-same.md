# Suite rahbar-same (20261124T053643Z)

Golden set: /app/eval/golden.jsonl (31 questions), seed 42, API http://api-candidate:8000, collection rahbar-same.

| Level | Metric | Value |
|---|---|---|
| module (embedding) | paraphrase mean cosine | 0.8239 |
| module (embedding) | unrelated mean cosine | 0.5545 |
| module (embedding) | gap | 0.2694 |
| module (embedding) | ms per chunk (mean) | 22.6849 |
| module (embedding) | determinism max abs difference | 0.0000 |
| component (retrieval) | recall_at_3 | 0.8654 |
| component (retrieval) | recall_at_5 | 0.9615 |
| component (retrieval) | mrr | 0.7885 |
| component (retrieval) | ndcg_at_5 | 0.8259 |
| end-to-end | faithfulness | 0.3333 |
| end-to-end | judged_answers | 15 |
| end-to-end | abstention_correctness | 1.0000 |
| end-to-end | false_abstention_rate | 0.4231 |
| end-to-end | citation_validity | 1.0000 |
| end-to-end | latency_p50_seconds | 1.8120 |
| end-to-end | latency_p95_seconds | 4.3940 |
| end-to-end | cache_hits | 0 |
