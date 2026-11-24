# D5: diagnosis of a real wrong answer (suite run `run1`, seed 42)

**Question h08:** "Which degree remark is given for a CGPA from 3.75 to 3.89?"
**Expected:** "Magna cum laude" (clause 7.2, PDF page 30). **System answer:** "I could not
produce a verified answer from the documents just now." (a false abstention).
Trace: `docs/evidence/a3/trace-h08-run1.json`, trace id `9e04846187974764815db6b6825bacb8`.

## What the trace shows, stage by stage

| Stage | Evidence in the trace | Verdict |
|---|---|---|
| Retrieval | clause 7.2 (page 30, score 0.786) is rank 1 and its text contains "CGPA from 3.75 to 3.89 Magna cum laude" verbatim | correct |
| Prompt | the context passed to the model holds that chunk first; nothing is truncated (`num_ctx` 8192) | correct |
| Generation | two attempts at seed 42, temperature 0.2 | **fault** |
| Guardrail | attempt 1 rejected: `citation ... section "7.2", page 7 does not match any evidence passage header` (the header says page 30). The retry made the same mistake. Action: `fallback`, reason `invalid_output` | working as designed |

**Root cause:** the 3B model (`llama3.2:3b`) copies the section and file name correctly but
writes the wrong page number in the citation. The citation validator is exact, so it
rejects the answer, and after one retry the system abstains. Retrieval, chunking and
the index are not at fault.

## How common is this

For the 26 answerable questions in run1, 11 were answered with the abstention message.
All 11 had the right chunk retrieved except one (draft-18, recall@5 = 0).

| Guardrail outcome | Count | Questions |
|---|---|---|
| `invalid_output`, wrong page or source in the citation | 3 | q06, h07, h08 |
| `invalid_output`, a sentence without an exact `[source / section]` tag | 5 | q08, q09, q12, h05, draft-19 |
| model declined by itself, no guardrail action | 2 | q02, draft-17 |
| model declined, retrieval also missed the clause (recall@5 = 0) | 1 | draft-18 |

So 8 of 11 false abstentions (73%) are citation-format failures after correct retrieval.

## Consequences

* Chunk size and overlap cannot fix it: all four chunking candidates kept recall@5 at
  0.9615 and none improved the abstention rate (see the Part C table in the report).
* The false-abstention rate of 42% is a generation-side weakness. It costs answers, but
  it does not produce wrong ones: citation validity stays at 1.00 and abstention
  correctness at 1.00.
* Candidate fixes, none applied yet: (1) tolerate a wrong page when the cited
  source and section match a passage, normalising the page from the header; (2) give the
  retry the exact list of allowed citations; (3) use a larger generator model. Each
  is a pipeline change and would need its own comparison contract in the gate.
