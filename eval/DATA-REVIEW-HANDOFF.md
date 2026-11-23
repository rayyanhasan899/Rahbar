# Assignment 3 dataset preparation and review

The existing partner-owned golden.jsonl is preserved. golden.synthetic-draft.jsonl
contains25 owned AI drafts:15 ordinary answerable,5 hard and5 unanswerable. Source
labels were derived independently from the actual cached 2026 rules PDF and visual
inspection of physical pages7,8,10; the exact PDF SHA256 is recorded on every row.
No label comes from retrieved results. Pypdf's duplicate hidden page text was not
accepted as physical-page proof; the visible rendered pages were inspected instead.
All rows are synthetic and reviewed=false. This is not a valid human-reviewed final
golden set. Moez must check pages himself, review at least8 synthetic rows, genuinely
write at least8 new human questions, and merge the chosen rows into golden.jsonl.
Do not change origin to human merely because a person reviewed an AI question.

live_queries.jsonl contains40 simulated user-style queries (28 intended in-domain,
12 intended outside the selected academic corpus). These are synthetic questions,
not a claim of observed production traffic or measured uncovered classifications.
The official E1 permits creating queries as if from users. In-domain wording is separately drafted; no live query is an exact copy of a golden draft question. E2 must measure similarities
and justify thresholds using the real pinned embedding model.

coverage-expansion-candidates.jsonl contains6 distinct AI candidate questions from
intended outside topics. It is not the final E4 expansion: select actual E2 uncovered
topics, review labels, preserve the old golden revision, add suitable questions and
measure before/after. No coverage increase is fabricated.

Generator: python scripts/prepare_assignment3_drafts.py (requires the selected cached
PDF and intentionally refuses to overwrite an existing live_queries.jsonl). The
checked-in data is the deliverable; a second generation needs an explicitly chosen
scratch checkout, not deletion of user work. No third-party PDF is committed.
