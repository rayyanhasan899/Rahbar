# ADR 0005: verified incremental ingestion and immutable publication

Date: 22 November 2026. Owner: Rayyan Hassan. Agent-assisted implementation.
Status: implemented on the Phase 1 branch; CO-05/06 interpretation awaits Moez's review.
Scope: Assignment 3 A1/A2 and ingestion F1/F2. This does not approve a production release.

## Context

A2 readers depend on `<collection>-control`, row `active`, with `active_collection`,
`generation`, `embed_model`, `dimension` and `versions`. API startup must not ingest.
Deleting live chunks before embedding replacements would break that safety contract.
Moez's proposed long-lived/delete-first collection and never-retrieve-history behavior
in `docs/a3/AI-TASKS-RAYYAN.md` conflict with the existing publication and historical
query contracts. This ADR records the implementation choice, not a fabricated approval.

## Document and configuration contracts

- `doc_id`: stable family from the manifest/front matter; filename stem is the fallback.
- `doc_version`: an orderable numeric version/date, from declared metadata or PDF date.
  Correct family IDs must be curated; the indexer cannot infer policy lineage reliably.
- `sha256`: exact incoming bytes. `doc_key`: first 32 hex characters of
  SHA256(`doc_id + NUL + doc_version`); not a path constructed from user metadata.
- Existing chunk `source`, physical `page` (1-based), `section`, `doc_version` and
  `superseded` remain. Publication adds `doc_id`, `doc_key`, `doc_sha256`, `archived`.
  Stable chunk IDs include the document key and existing content/position identity.
- A fingerprint binds embedding model name, Ollama `/api/tags` digest, chunk size,
  overlap, document-embedding text bound and extraction/verification profile.
  A different fingerprint needs a new collection prefix, not reuse of old vectors.
  Dimension must also agree. Prefixes are 2–29 safe characters to fit snapshot names.
- The API still checks its existing model/dimension contract. Query-time digest
  validation and trace recording are Phase 2 integration work, not claimed here.

## Four checks and classification

Every input gets `quality`, `completeness`, `recency`, `uniqueness`, each with
`passed` and `reason`. Failures in extraction are isolated per input. Required title,
source, version/date, actual page count, optional declared-page agreement, PDF EOF,
text ending, printable/meaningful text and finite embedding checks fail closed.
These are heuristics, not proof of semantic completeness or OCR accuracy.

Exact hashes and cosine against another family's document vector implement uniqueness.
Same-family changed versions are legitimate. Document embeddings use the first
`DOCUMENT_EMBED_CHARS` (default 4000, allowed 64–16000); they are a bounded proxy,
not full-document semantic equivalence. Threshold .995 is provisional and must be
calibrated on the actual pinned model in Phase 3. Rejected near-duplicate analyses
are cached, so rejection does not secretly reembed on every run. Uniqueness finishes
before chunking; failed inputs never receive chunk embeddings or enter the index.

Recency PASS means the version can be ordered and family selection succeeds.
Previously accepted older versions are archived with a reason naming the active
version. Invalid/unorderable inputs fail and quarantine. Thus no failed input is
silently indexed under an exception to A1. Older verified chunks retain
`superseded=true, archived=true`: default retrieval excludes them; existing explicit
historical-year retrieval is preserved. No golden question/label was altered.
This explicit interpretation needs partner review against A1/A2, CO-05/06.

## Incremental publication and crash recovery

1. Take the existing shared `/locks` flock. Manual, weekly, verify and rollback writers
   use the same lock. CronJob `Forbid` alone is insufficient for manual Jobs.
2. Discover complete configured input scopes, validate confined paths and manifest
   hashes, extract/verify, then reuse content/config analysis and accepted vectors.
   `INCOMING_DIRS` is a comma-separated list; empty means `CORPUS_DIR`.
   Missing configured folders fail before deletion. Unscanned scopes remain unchanged.
3. Bad updates preserve the last verified document. Inputs absent from a scanned scope
   become deleted (zero current chunks), except a verified newer family replacement
   archives the prior version. Duplicate incoming family/version identities quarantine.
4. Write content-addressed source blobs/cache, then an immutable ledger revision
   **before** it can be referenced by the published pointer.
5. Stage `<collection>-<run uuid>` using cached vectors, in at most 128-row adds.
   Unchanged documents are physically copied to the snapshot without reembedding.
   Validate total/per-document counts, exact chunk IDs and archive/provenance metadata.
6. Upsert the existing control row only after validation. Extra fields include
   `ledger_revision`, fingerprint, digest, chunk settings and content hash. API/cache
   consumers retain their existing generation invalidation mechanism; no Redis access
   is granted to the indexer. Identical content/status/pins and valid storage keep the
   original generation and make zero document/chunk embedding calls.
7. Materialize convenience current/archive views and `ledger.json`. On restart, the
   pointer-selected immutable revision is authoritative, not convenience `ledger.json`.
   A crash before publication leaves the previous live collection; a crash after it
   repairs convenience views on the next compatible ingestion run.

`pipeline.counts` compares actual published rows to the ledger and reports each
family/version/status, including deleted zero rows. Orphan absence is asserted only
for the **published generation**, not for intentionally retained old collections.
Rollback pins a previously verified version, stages cached vectors and publishes;
unpin chooses the newest eligible version. Neither operation reembeds or rereads
incoming documents. A pinned version remains selected through ingestion.

## Persistence and limits

`/datalake/state/<collection>/revisions/` stores immutable ledgers.
`current/<collection>/<hashed family>/<hashed version>/` and
`archive/<collection>/<hashed family>/<hashed version>/<sha>/` are convenience views.
`objects/<sha>/<source>` and `cache/<fingerprint-and-input hash>.json` retain recoverable
bytes/vectors. `quarantine/<run>/<hashed location>/` and `reports/` preserve reasons.
Collection-scoped views prevent candidate indexing from overwriting live views.
`--verify-only` writes quarantine/report artifacts but publishes no ledger/index and
does no chunk embedding; uncached document similarity can still call the model.

Old snapshots, immutable blobs, failed staging collections and quarantine are retained.
This costs storage and needs an explicit retention/garbage-collection policy after
review; deleting them automatically could break in-flight readers or recovery.
The initial 1 GiB data-lake claim needs measurement/monitoring on the run host. Source
extraction and per-document JSON caching still hold one document's text/chunks in
memory; embedding requests are batched (default 16), not an unlimited request. Live
peak memory, PVC persistence, actual Chroma and concurrent Jobs remain Phase 3 proof.

## Verification

`indexer/tests/test_incremental.py`, `test_verification.py`, `test_corpus_transfer.py`
use temporary files, deterministic fake vectors and fake storage/cluster calls.
Existing `test_pipeline.py` proves cross-process flock exclusion on Linux. CI also
builds the actual indexer image and validates manifests. See the Phase 1 report for
actual runs and the separate pre-existing UI scan blocker. No model score, live
Kubernetes observation or human review is inferred from these tests.
