# Controlled pipeline failure analysis

The actual A/B/C/E experiments ran on isolated collections in real audit
[42308165966](https://github.com/rayyanhasan899/Rahbar/actions/runs/42308165966),
source 4917e45. The live publication was not damaged. Raw measurements are
[failures.json](evidence/day3-audit-4917e45/failures.json). Each ablation restores
or compares against the same unchanged 700/100 reference, with the original
document-derived labels. The separate source-derived two-clause diagnostic for C was also executed.
We do not invent a regression where the original golden set showed none.

## Stage A — extraction: disable OCR

**What was broken:** read the image-only Faculty Entrepreneurship / Technical
Start-ups PDF through its text layer without OCR. This is one selected public
source, not a fabricated empty fixture.

**Observed symptom:** all eight physical pages produced zero text characters.
The restored OCR counts were 2717, 2569, 1782, 1024, 1088, 1750, 536 and 372;
all eight pages were OCRed. Questions about this source would have no indexed
text even though the download and page inventory looked healthy.

**Diagnosis as if unexpected:** compare source byte hash/page count with per-page
extracted character counts; inspect the PDF visually and run the pipeline's
structured extraction log. A valid PDF download does not establish a text layer.
The diagnostic metric is eight empty pages before OCR versus zero after it.

**Remedy and restored state:** enable bounded page-at-a-time OCR at 200 DPI,
Tesseract single-threaded, retain page metadata and fail visibly on OCR errors.
The restored count above was actually measured. Six unrelated blank/artwork pages
elsewhere in the corpus remain disclosed; this remedy does not invent their text.

## Stage B — chunking: flat 100-token windows, no overlap

**What was broken:** replace section-first chunking with flat 100-token windows
and zero overlap. Attribute each window to its starting section/page, even when
it crosses a boundary. This models an actual boundary/attribution defect; the
reference labels were not rewritten after seeing retrieval.

**Observed symptom:** macro recall@5 fell from 11/13 (84.6154%) to 3/13 (23.0769%).
q01, q02, q04, q06, q07, q10, q12 and q15 lost their labelled relevant sections.
The broken chunks were stored/queried in a separate collection, rather than
pretending a code change alone proves degraded retrieval.

**Diagnosis as if unexpected:** inspect retrieved chunk IDs, source/section/page
and the source boundary around each lost clause. Compare recall by question and
chunk metadata, not only the model's final words. Exact words can survive while
their section label/exception has been cut away.

**Remedy and restored state:** restore paragraph/sentence-aware boundaries with
700/100 lexical-token budget and overlap inside a section. Reference retrieval
measured 84.6154% again; its generation/control collection is retained in the raw
artifact. The live index was unchanged throughout the isolated ablation.

## Stage C — retrieval budget: top-k 1

**What was broken:** reduce the retrieved context from five passages to one,
with the same index, embeddings, question and current/historical filters.

**Observed symptom:** the context budget fell to one passage, but the original
15-question set's macro recall stayed 84.6154%. Each answerable label needs only
one section, and the eleven successful questions already placed it first. It
would be false to report a recall regression on these measurements. Two original
misses remain misses at both k values.

**Diagnosis as if unexpected:** compare the actual returned reference list length
and per-question relevance coverage. A one-clause benchmark cannot demonstrate
coverage of a question requiring two clauses. This is a measurement limitation,
not evidence that top-k 1 is universally sufficient.

**Remedy and restored state:** restore top-k 5 (observed reference recall 84.6154%)
and add a separate source-derived diagnostic asking both opposite Theory/Lab
repeat decisions. eval/failure-probes.yaml labels clauses 4.7 and 4.8 from the
current policy; these already support original q05/q06 independently. The original
golden labels and baseline remain untouched. The actual follow-up diagnostic measured **0.5 recall at k1** and **1.0 at k5**:
clause 4.7 alone was returned when k=1, while k=5 restored both 4.7 and 4.8.
Both clauses appear on physical page 20. This genuine coverage failure and
restoration are stored under C-top-k.additional_diagnostic; its scores are not
folded into the unchanged golden baseline.

## Stage E — source/version filtering: disable the predicate

**What was broken:** query the same collection with no current/superseded or
explicit historical-version predicate.

**Observed symptom:** macro recall again stayed 84.6154%, while forbidden versions
entered context. Current q09 included the superseded 2023 clause 4.25; historical
q10 included four 2026 passages alongside its 2023 evidence. Default current
questions q01/q02/q03/q04/q07/q08/q11/q12/q14/q15 also received superseded passages.
This creates real contradictory-policy exposure even though the labelled correct
source still appears somewhere in the top five.

**Diagnosis as if unexpected:** inspect doc_version/superseded for every returned
chunk and compare with the requested year, rather than relying on aggregate recall
alone. For q09/q10 the independently checked withdrawal deadlines differ: last day
of makeup week (2026) versus last day of classes (2023). Mixed context is a policy
failure even when a relevant-label membership metric remains unchanged.

**Remedy and restored state:** reinstate version_filter: ordinary questions require
superseded=false; explicit year requests only matching recorded versions. The
restored reference lists contain only permitted versions, while retaining the
same measured recall. No network policy or indexer Redis access was added.

## Additional real failures discovered during Day 3

The first real model audit exposed confident uncited refusals. Contradictory
flags/confidence now get the single retry; valid declines are canonical and
cannot leak uncited facts. The 8192-context/prompt retest produced real cited
answers and passing golden gates. The exact contribution of each prompt/context
change was not isolated. Cache headers were correctly uppercase; the audit's
lowercase expectation was fixed. A saved 502 response revealed that rollback
acceptance was too weak; the corrected audit now requires HTTP 200 and the exact
original UI hash. The negative response bytes are preserved as
rollout-restored-502.html.txt, not edited into a passing page. These discoveries
are separate from the four controlled ablations above.

The corrected audit 42308165966 passed all eleven acceptance checks, including
uppercase cache headers, live reindex/manual writer serialization and original-UI
HTTP 200/hash restoration. Earlier failed evidence remains archived separately.
