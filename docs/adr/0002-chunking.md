# ADR 0002: Structure first, measured lexical-token budgets

Status: Accepted 700/100 after fresh deployed-image measurements, 7 November 2026.

## Context
Policy clauses, definitions and table rows are meaningful boundaries. Fixed
character windows can cut a condition away from its exception. The golden
questions were committed in d7b5e88 before the first retrieval experiment.

## Decision
Identify Markdown headings and numbered PDF clauses, group their content,
then prefer paragraph/sentence endings under a token budget. Oversized
sentences use bounded token windows. Overlap applies within a section, not
across unrelated clauses. A chunk records its starting physical PDF page;
its section may continue across pages. For Markdown fixtures, numbered
sentences stay under their Markdown heading so the supplied relevance labels
remain stable.

The budget uses Unicode lexical tokens: words plus individual punctuation,
not the Ollama model's subword tokenizer. This is reproducible without an
additional tokenizer/model dependency. We report that distinction explicitly.
Embedding truncation is disabled so overlong embedding inputs fail visibly rather
than silently dropping evidence. Chunk IDs hash source/version/section/page/
offset/text. Preserve original document names in metadata.

## Measurements
Test (300,40), (500,75), (700,100), with the same model, golden set and
non-superseded filter (explicit historical requests opt into their version).
Compute recall@3/@5 over answerable questions, excluding empty relevance;
storage amplification is stored lexical tokens / cleaned original tokens.
The reproducible command and actual results belong in docs/PIPELINE.md and
eval/chunk-experiments.json. Do not invent a winning result.

## Consequences
Clause-level chunks can be smaller than the requested target, so increasing
the budget need not improve recall. OCR errors and layout duplication remain
possible. Dedicated hybrid retrieval is Day 2/3 work only if exact-term
measurements justify it; no benchmark labels are encoded in retrieval logic.

Measured results: all three candidates achieved 11/13 recall@5. Chunk counts were 647, 565 and 536; amplification was 1.089832, 1.078163 and 1.061650. Choose 700/100 provisionally for lower duplication at equal measured recall.

Fresh augmented-extraction run 42308165966 confirms equal 11/13 recall@5.
The independently recorded fresh configurations contain 738/671/646 chunks and
amplification 1.061133/1.047257/1.029494. Choose 700/100 for lowest duplication at
equal measured recall. Historical Day 1 figures above describe the earlier profile;
eval/chunk-experiments.json and PIPELINE.md hold the current measured profile.
