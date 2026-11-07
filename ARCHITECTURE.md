# RAHBAR architecture

Ingress routes `/` to nginx and `/api` to three FastAPI readers. Redis provides
shared persistent semantic caching; Chroma 1.0.12 is a one-replica StatefulSet
with volumeClaimTemplates for stable identity/storage. Redis uses an AOF-backed
PVC. Neither backend is exposed by Ingress. Chroma disables Service-link
injection to avoid `CHROMA_PORT=tcp://...` conflicting with its numeric setting.

The API only reads an index. A separate Job performs extraction/OCR, cleaning,
structure-aware overlapping token chunks, bounded embedding batches and storage.
A weekly CronJob uses the same image/arguments. All writers hold a shared PVC
file lock across the complete operation; CronJob Forbid alone cannot serialize
manually created Jobs. The curated corpus resides on a separate PVC.

The writer creates a staging collection, records model/dimension/cosine metadata
and stable chunk IDs, validates count, then publishes a collection/generation
pointer. Failed staging does not replace the live collection. Old collections
are retained; destructive automatic collection cleanup is absent. Readers check
both pointer and collection model/dimension. Mismatch makes readiness fail;
no API startup ingestion or mixed-model query is permitted.

Current retrieval excludes superseded documents; an explicit year requests that
historical version. Query/document embedding prefixes share one pin. Questions
and bounded turns feed retrieval and generation. Output must validate against
the response schema, resolve citations to retrieved passages and attribute every
factual sentence with a known inline citation. One retry precedes safe fallback.
Untrusted document text is delimited and flagged. The UI renders text, not model
HTML, and flagged requests cannot reuse cached output.

Cache namespaces include publication generation, model/provider, prompt/schema
digest and retrieval settings. Reindex invalidates cached answers without an
indexer-to-Redis path. Per-entry expiry prevents unrelated writes renewing old
entries. Numeric/year and directional intent checks reject misleading semantic
near-duplicates. Threshold selection uses recorded positive/negative pairs.

Default deny permits DNS, Ingress-to-UI/API, UI-to-API, API/indexer-to-Chroma,
API-to-Redis and selected provider /32 egress. UI-to-Chroma and indexer-to-Redis
are absent. Workloads have dedicated ServiceAccounts without mounted tokens,
non-root identities, read-only roots, dropped capabilities and explicit writable
volumes. Private backend/model HTTP is a documented residual limitation.

Bounded startup checks, dependency-free liveness and truthful readiness serve
different purposes. Rolling updates use maxSurge 1/maxUnavailable 0, preStop and
termination grace. HPA ranges from 3 to 8 on CPU; waiting for the model can raise
latency without API CPU load. JSON logs and Prometheus metrics expose retrieval,
generation, cache, retries, abstention, tokens and injection flags.

Bootstrap creates dependencies, transfers verified sources, completes indexing,
then waits for API/UI. Fixture CI uses real embeddings and an explicit stub
provider. The separate real audit uses public policies and real Ollama. CD tests,
publishes and deploys the actual merged main SHA. See the four ADRs for decisions
and requirement records for what has actually been demonstrated.
