# FAST-NUCES public academic policy corpus

Verified 5 November 2026. Eight selected public documents: six PDFs with **194
physical pages**, plus two HTML pages (not counted toward the 40-page minimum).
All nine suggested sources downloaded, including the formerly problematic 2023
rules. The extra 2023–24 annual report was excluded from the final selection:
it added no required property and required substantially more graphical OCR.
The download inventory records that exclusion; no source was fabricated.

| Required property | Selected evidence | Verification |
|---|---|---|
| At least six documents and forty pages | Rules 2023:26; rules 2026:58; prospectus rules:5; student handbook:64; annual report 2019–20:33; startup policy:8; fee and grading HTML | Physical PDF inventory and SHA-256 manifest |
| Genuine policy version pair | Undergraduate rules August 2023 and academic rules June 2026 | Clause 4.25 changes withdrawal from last day of classes to last day of makeup week; old physical p16 visually inspected |
| Scanned image-only PDF | Faculty Entrepreneurship / Technical Start-ups Policy | All eight pages have no useful extracted text layer; all eight OCRed and yielded text |
| Informative table | Rules handbook physical p12 grade-point table; fee/grading HTML | Two tables detected on p12; table-audit.json records a small sample |
| Long definitions | Student handbook and current rules Generative AI policy | Multi-page structured acceptable/unacceptable-use definitions and subsections |
| Deliberately absent topic | Campus Wi-Fi configuration/password-reset procedures | IT setup/reset guides excluded; golden q13/q14 request those missing procedures |
| Exact terms | Clauses 1.21, 4.25 and 5.4; CGPA/attendance thresholds; fees/grade points | Golden exact-term cases and source clauses |

## Provenance and permitted use
Only public university URLs were used, never authenticated SLATE/Flex/mail.
`corpus/sources.yaml` records version/superseded choices. The existing serial
fetcher pauses between downloads, normalizes URLs, records hashes and reuses
downloaded bytes. `python corpus/fetch.py --verify` rechecks the manifest.
Third-party PDFs, HTML and extracted full text remain ignored under corpus/raw
and .venv. Commit the fetcher, source list, manifest and small diagnostic
evidence, not downloaded third-party documents. Source rights remain with their
owners. The first draft PR (#1) names this corpus.

The 2023 policy is superseded for default retrieval but retained for explicit
historical questions. Annual-report editions describe their stated reporting
periods rather than claiming to be current student policy. Current documents
may repeat clauses; evaluate by source/section identity, not duplicate hits.

## Extraction audit and limitations
`docs/evidence/extraction-audit.json` records actual OCR and remaining empty
pages. OCR recovered 24 pages in the older rules, 5 in current rules, 4 in the
student handbook and all 8 startup-policy pages. Six pages remained empty after
OCR; do not claim they contain recovered text. Blank/artwork pages require
visual judgment. OCR can misread punctuation/numbering and diagram labels.
The older withdrawal clause was checked visually against its OCR before use.
The table audit demonstrates column ambiguity in linear text. The extractor
also supports explicit pipe-delimited table rows; full table/diagram accuracy
still requires human review. No claim is made that every table is lossless.

Reproduce extraction with `python scripts/audit_corpus.py` after fetching.
Cached extracts are ignored, contain third-party text, and are never submission
artifacts. Regenerate them after changing extraction/cleaning rules.

## Day 3 live-source and deployed-image audit

Run 42294051804 re-fetched the selected public documents serially, verified all
eight hashes and compared the snapshot to the committed manifest. The actual
indexer image extracted and published 646 chunks at 700/100. A separate fresh
extraction inside that same image produced the profile/fingerprint audit in
docs/evidence/day3-audit-54f37ff/extraction-audit.json: Tesseract 5.3.0,
Poppler 22.12.0 and pdfplumber 0.11.10. The six empty pages remain disclosed;
OCR/table interpretation is not assumed lossless. Physical page counts and the
pre-tuning golden source/section labels were not changed to fit retrieval.
