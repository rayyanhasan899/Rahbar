# Real-corpus evaluation provenance

The baseline is a genuine first passing real-model run, not the fixture corpus
and not a fabricated target. It was created explicitly by --update-baseline only
after all absolute gates passed, in GitHub run 42294051804 at source
54f37ff2ee954d70ac76ad8fd7716695654e0610. The final measurement from that same
cluster is eval/results.json. Both contain 15 unchanged golden questions,
recall@5 11/13 (0.8461538462), nine valid citations out of nine, and both
must-abstain cases refused. Nine questions received grounded answers; four other
answerable/injection questions safely declined or fell back. Citation membership
is not semantic entailment or a claim that all answerable questions were answered.

The complete audit failed its cache-header assertion (the API correctly returns
uppercase HIT/MISS). Its rollout restoration check also proved too weak: raw
rollout-restored.html is a 502 page. Those runtime requirements remain unverified
until the corrected rerun; passing golden metrics do not erase those failures.
The raw report is preserved under docs/evidence/day3-audit-54f37ff.

Model: llama3.2:3b, temperature 0.2; embeddings nomic-embed-text, 768 dimensions,
digest 0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f.
Corpus: pinned public eight-document manifest, live fetched and hash-verified.
Golden SHA256: 0717f7074bc4f04b4f164c831f21c5d516baab90875f3418ce39782aee4a652a.
Chroma client/server 1.0.12; chunk budget 700/100 lexical tokens; 646 chunks.
Fresh extraction ran inside the actual indexer image: Tesseract 5.3.0,
Poppler 22.12.0, pdfplumber 0.11.10. The recorded fingerprint also covers extractor,
cleaner and dependency locks; full source documents/extraction caches stay ignored.

Initial/final measurement used candidate relevance floor 0.45. Measured minimum
answerable top score 0.6956296 and maximum absent-topic top score 0.6250884 justify
raising the shipped floor to 0.65. The next real run must compare to this genuine
baseline without updating it. No relevance labels are changed. Results refer
to the original runner path in their golden field; eval/golden.yaml is the same
hashed input in this repository.
