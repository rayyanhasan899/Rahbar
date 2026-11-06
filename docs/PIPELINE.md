# Indexing and evaluation pipeline — Day 1

## Extraction and cleaning
PDF pages are processed individually. Pages with fewer than ten word characters
are OCRed at 200 DPI, one rendered page at a time, with a 120-second OCR timeout.
Tesseract OpenMP concurrency is limited to one thread to avoid oversubscribing
the small laptop. An early blank/artwork-page OCR timed out during simultaneous
builds; retrying with bounded threads completed the selected corpus. OCR errors
fail indexing visibly rather than publishing a partial replacement index.
PDF ruled tables can also be emitted as pipe-separated cells. HTML drops
script/style/nav content and retains table-cell separators. Markdown removes
front matter but preserves fixture headings; text input is supported.

| Example | Before linearization | After explicit cells | Limitation |
|---|---|---|---|
| Grade-point table, current rules physical p12 | A+ 4.00 C+ 2.33 | A+ / 4.00 / C+ / 2.33 in four ordered columns | Empty layout rows and multiple side-by-side pairs need review |

The small measured sample is in docs/evidence/table-audit.json. Repeating margin
lines occurring on at least 70% of pages (minimum three) and standalone page
numbers are stripped conservatively. Numbered clauses and headings are not
stripped merely because they repeat. NFKC normalization and horizontal-space
cleanup are applied. We deliberately retain clause numbers, table values and
policy exceptions. Header/footer detection is heuristic, not layout perfection.

## Chunking
Sections precede paragraphs and sentences. Oversized sentences fall back to
bounded token windows; overlapping neighbors stay within a section. Metadata
records the starting physical PDF page, not the printed page number. Lexical
tokens are Unicode words plus punctuation, not model subword tokens. Document
source/version/section/page/offset/text determine stable chunk IDs.

| Size (lexical tokens) | Overlap | recall@5 | Chunks | Amplification |
|---:|---:|---:|---:|---:|
| 300 | 40 | 0.846154 | 647 | 1.089832 |
| 500 | 75 | 0.846154 | 565 | 1.078163 |
| 700 | 100 | 0.846154 | 536 | 1.061650 |

Stored tokens / cleaned original tokens is storage amplification. The golden
set was committed before the experiment (d7b5e88); do not relabel questions from
retrieval output. The experiment excludes absent-topic cases from recall and
keeps per-question top-five evidence. It is retrieval-only, not a generation
baseline. Final size selection follows measured results, not these candidates.

## Embedding and storage
The shared EMBED_MODEL is nomic-embed-text; actual host probe returned dimension
768. API and indexer use the same model, with search_query/search_document
prefixes for that model. Ollama inputs are batched (default 16), finite/equal
dimensions validated, HTTP calls bounded and truncation disabled. Record the
installed model digest with final deployment evidence; a tag alone does not
protect against someone replacing the host's model bytes.

Chroma thin client and server are both 1.0.12. Store id, text, vector, source,
section, starting physical page, doc_version and superseded. A staged cosine
collection becomes active only after count validation. Control metadata records
the generation, model, dimension, available versions and content fingerprint.
See ADR 0001 for shared-PVC locking, publication and old-generation retention.
The API reads the pointer and refuses readiness for mismatch/empty data. It
never runs ingestion at startup.

Real-corpus delivery to the cluster is not yet configured: Day 1 uses the
explicitly labelled dummy Job for infrastructure proof. Local extraction and
real embedding/retrieval experiments are separate. Day 2 must supply a corpus
volume and remove --dummy only after model egress/pins are configured. The
weekly CronJob stays suspended while its template is a dummy bootstrap.

## Evaluation method and gates
Recall matches exact (source, section) pairs after converting section values
to strings. Repeated relevant labels/hits count once. Questions without known
relevant passages return null recall and are excluded from macro means.
Report recall@3 and @5 overall and by type. Citation validity is micro-averaged
across individual citations and requires matching source/section and page when
provided. No citations return null, not a fabricated 100%. Answered responses
without citations fail the gate separately. Abstention requires the literal
boolean false; missing fields do not count as a refusal.

Missing baseline, missing/nonfinite scores, no must-abstain cases, any incorrect
abstention, citation validity below 0.95, or recall@5 more than 0.05 below the
baseline fail closed. Exactly five percentage points is permitted. Explicit
baseline updates still must pass the absolute quality checks. Unit tests cover
boundaries, duplicate hits, invalid citations, empty sets and absent baselines.
Do not compare the tiny fixture corpus to the real-corpus baseline.

## Semantic cache — Day 2 dependency
Redis will be shared by API replicas. The configured 0.95 threshold and 0.45
relevance floor are initial candidates, not measured shipped values. Try 2–3
cache thresholds, record a false hit and select the lowest zero-false-hit value.
Never cache follow-ups, abstentions, out-of-scope or invalid answers. Namespace
entries by published index generation; indexer never contacts Redis. Cache and
grounded generation are not complete on Day 1 and no scores are invented here.


## Actual Day 1 measurements
All three configurations measured recall@3 = recall@5 = 11/13 (84.6154%).
The two absent-topic questions are excluded from recall, not counted as hits.
These are retrieval scores, not evidence of generation/citation/abstention
correctness. At equal measured recall, 700/100 uses the fewest chunks and
lowest amplification, making it the initial candidate. The default dummy
bootstrap size is not a claim of a final tuned production deployment.

The immutable input snapshot and source/model fingerprints are included in
eval/chunk-experiments.json. The experiment used the initial cleaned extraction
profile from revision 257b8f0; explicit PDF table-row augmentation was added
later and is unit-tested but must be retuned before final shipping. Do not
silently reuse old extraction caches after changing extraction rules. The
current golden set measures its designated reference source/clauses; omitted
equivalent sources must be audited independently, not relabelled from hits.

The misses were q08 (add/drop deadline, reference clause 4.19) and q09
(current withdrawal deadline, reference clause 4.25). For q08, the top hits
included equivalent student-handbook material; for q09, nearby clauses 4.24
and 4.23 crowded the result list. Version questions measured 50% recall@5,
ordinary 87.5%, and exact/injection questions 100% on this small set. Exact
terms were not the worst category in this run. Day 2 should independently
audit relevance coverage, deduplicate near-identical hits, and investigate
lexical/hybrid reranking without changing labels to flatter the score.

The real indexer CLI also ran all five stages on the owned Markdown fixtures,
published 12 chunks using real 768-dimensional embeddings, and exited zero.
See docs/evidence/day1-real-fixture-indexer.txt. The Kubernetes bootstrap Job
remains explicitly dummy; those two evidence sets are intentionally labelled.
