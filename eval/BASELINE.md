# Real-corpus evaluation provenance

The baseline is a genuine first passing real-model run, not the fixture corpus
and not a fabricated target. It was created explicitly by --update-baseline only
after all absolute gates passed, in GitHub run 42294051804 at source
54f37ff2ee954d70ac76ad8fd7716695654e0610. The latest final measurement from the corrected source-4917e45 audit
42308165966 is eval/results.json; it compares against this preserved baseline. Both contain 15 unchanged golden questions,
recall@5 11/13 (0.8461538462), valid citations for every cited answer, and both
must-abstain cases refused. The baseline answered nine questions; the final source-4917e45 measurement
answered eight. Other answerable/injection questions safely declined or fell back. Citation membership
is not semantic entailment or a claim that all answerable questions were answered.

That first complete audit failed its cache-header assertion (the API correctly returns
uppercase HIT/MISS). Its rollout restoration check also proved too weak: raw
rollout-restored-502.html.txt is a 502 page. Those first-run runtime claims were not valid; the corrected rerun below
subsequently verified them; passing golden metrics do not erase those failures.
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

The corrected audit 42308165966 passed all eleven runtime checks at shipped floor
0.65, including live cutover, manual writer waiting and HTTP-200 exact-body rollback.
Final recall drop is zero, citation validity 1.0, must-abstain failures zero. The
baseline file was preserved, not updated to flatter the subsequent result.
