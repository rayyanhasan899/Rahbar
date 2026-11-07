# Indexing and evaluation pipeline

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
| 300 | 40 | 0.846154 | 738 | 1.061133 |
| 500 | 75 | 0.846154 | 671 | 1.047257 |
| 700 | 100 | 0.846154 | 646 | 1.029494 |

Stored tokens / cleaned original tokens is storage amplification. The golden
set was committed before the experiment (d7b5e88); do not relabel questions from
retrieval output. The experiment excludes absent-topic cases from recall and
keeps per-question top-five evidence. It is retrieval-only, not a generation
baseline. Fresh image-matched measurements from run 42294051804 select 700/100: equal
recall and lowest measured amplification. The cleaned input contains 74,592
lexical tokens. Model dimension is 768; the JSON records the source fingerprints.

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

Day 3 supplies the real corpus through a hash-verified PVC transfer. The Job
and weekly CronJob use real indexing, the same model pin and a common writer
lock. Staging publication changes the cache generation without Redis access.
The dependency-first bootstrap waits for completed indexing before API readiness.
The prior Day 1 dummy evidence remains labelled as historical infrastructure proof.

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

## Query pipeline — Day 2
Implemented in api/app/services/ (ADR 0003): injection flag on the question,
follow-up query building, semantic cache, retrieval, removal of instruction-like
sentences from passages, relevance floor, generation with one validated retry,
safe fallback, cache store. Offline tests: api/tests/test_answer_pipeline.py,
test_providers.py, test_guard_and_cache.py, test_ask_route.py.

### Relevance floor
The genuine real-corpus run measured minimum answerable top score 0.6956296
and maximum must-abstain top score 0.6250884. The shipped 0.65 lies between them.
This small calibration set cannot guarantee separation for unseen questions;
low relevance, schema/citation validation and safe model refusal remain separate
guards. Reproduce the margins with `python scripts/score_margins.py eval/results.json`.

| Run | Lowest answerable top score | Highest must-abstain top score | Floor shipped |
|---|---:|---:|---:|
| 54f37ff calibration; 4917e45 retest | 0.6956296 | 0.6250884 | 0.65 (real gate passed) |

### Semantic cache
Redis, shared by all replicas, namespaced by index generation plus embedding
model, provider and LLM model, so a reindex invalidates old entries without the
indexer touching Redis. A hit needs cosine >= CACHE_THRESHOLD and identical
numbers (years, clause numbers) in both questions. Never stored: follow-ups,
declined answers, fallbacks, instruction-like questions. Bounded at
CACHE_MAX_ENTRIES per namespace (oldest evicted) with CACHE_TTL expiry.

Threshold experiment: five predeclared paraphrases, five predeclared negatives,
and 103 further negatives derived from unequal pre-existing golden relevance
sets, for 113 comparisons. Labels are independent of retrieved results. The
expanded local run used the real nomic model and records every similarity and
guard result in eval/cache-threshold-experiment.json. A fresh remote rerun also
records model digest, dimension and input hashes.

| Threshold | Guarded paraphrase hits / 5 | Guarded false hits / 108 |
|---:|---:|---:|
| 0.65 | 5 | 3 |
| 0.70 | 4 | 1 |
| 0.75 | 4 | 0 |
| 0.80 | 4 | 0 |
| 0.85 | 2 | 0 |
| 0.90 | 0 | 0 |
| 0.95 | 0 | 0 |

The shipped 0.75 is the lowest tested threshold with zero false hits on this
set, not a proof of zero production errors. At 0.70, degree duration versus
minimum graduation CGPA passes the guards at cosine 0.718278 despite different
answers. Theory-pass/Lab-fail versus Lab-pass/Theory-fail measured 0.9954: no
practical similarity threshold alone fixes that error, so directional intent
is an additional eligibility check. Per-entry timestamps enforce expiry even
when other entries renew a Redis hash TTL. Namespace v3 also includes generation,
provider/model, retrieval settings and prompt/schema digest.

### Prompt injection
Two layers: the prompt marks passages and question as data, and guard.py replaces
instruction-like sentences in passages before generation. The fixture's planted
line (academic-rules-2026.md, 3.2) is replaced; see
test_poisoned_passage_never_reaches_the_model. Questions containing such text are
answered from evidence but never cached. Counter: rahbar_injection_flags_total.

### CI evaluation gate
Job e2e-eval indexes eval/fixtures with the real pipeline (nomic-embed-text in a
pinned Ollama container, Chroma 1.0.12), runs the API with the stub LLM and gates
on eval/run_eval.py against eval/fixtures/baseline.json. The committed fixture baseline/results came from a genuine indexed local run.
The real-corpus baseline is a separate explicit first passing measurement; it
must never be replaced by fixture scores or relabelled to flatter a regression.

## Historical Day 1 measurements
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
See docs/evidence/day1-real-fixture-indexer.txt. That Day 1 Kubernetes bootstrap Job was explicitly dummy. Day 3 manifests
select real indexing; current cluster acceptance status is recorded separately.

## Real generation and extraction verification

Run 42294051804 used the actual image profile (Tesseract 5.3.0, Poppler 22.12.0,
pdfplumber 0.11.10). Source files were live fetched and all eight hashes matched.
The image ran fresh extraction before the three chunk experiments; no old laptop
cache was silently reused. See docs/evidence/day3-audit-54f37ff/extraction-audit.json.
The baseline was established explicitly after absolute gates passed; final scores
matched it at recall@5 0.846154, citation validity 1.0, abstention correctness 1.0.
Nine of fifteen questions received cited answers; four answerable/injection cases
safely declined or fell back. This limitation is distinct from citation validity.
The real poisoned owned fixture was actually indexed; its model responses safely
refused/fell back rather than obeying the planted instruction. It did not prove a
useful answer to every poisoned question. Raw evidence is poison-probe.json.

The initial 4096-context audit exposed uncited confident refusals. Responses now
canonicalize valid refusals, retry contradictory confidence/flags once and require
sentence-level exact citation tags for answered content. Ollama context is bounded
at 8192/output512, with a prompt-token safety margin; longer inputs fail closed.
A format example explains true/false output shape. The 54f37ff retest produced real
cited answers; the precise causal contribution of the context/prompt changes was
not isolated. Temperature is 0.2 for low-variance factual JSON, not a guarantee
against hallucination.

The corrected full audit 42308165966 at source 4917e45 passed at floor 0.65.
It preserved the genuine baseline and measured zero recall regression, citation
validity 100%, no answered must-abstain cases, and eight cited answers out of
fifteen total questions. Other cases safely declined/fell back. Its 47 cutover
probes stayed HTTP 200; generation changed at the same 646 chunks, a cache MISS
crossed publication and later requests HIT. The manual writer waited 208.441 s
on the shared lock. Actual source-equivalent repeated extraction/chunk experiments
and failure artifacts remain separate from the live publication.
