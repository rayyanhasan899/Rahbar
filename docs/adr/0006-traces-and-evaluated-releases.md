# ADR 0006: request-time evidence and coherent evaluated releases

Date: 22 November 2026. Owner: Rayyan Hassan; agent-assisted.
Status: implemented; genuine partner review and live demonstrations pending.

Each handled POST /api/ask creates one request-local Trace, including validation and
retrieval errors. ContextVars isolate threads/requests. Providers capture the actual
sanitized transport messages, bounded passage context, model options and retry prompts;
no model reasoning or authorization headers enter evidence. AskResponse keeps every
existing field and adds evidence. Request_id equals trace_id. A frozen collection
snapshot prevents cache embedding and retrieval observing different publications.
Embedding artifact digest is checked before querying a new pinned index; legacy
unknown digests remain unknown and cannot satisfy evaluation provenance.

Stdout JSON and /traces/traces-<pod>.jsonl carry the same record. File/process locks
serialize append; record/file budgets and short lock acquisition expose failure in
persistence.error and a counter rather than breaking answers. Existing traces are
never silently overwritten. Export/rotation is an operational action; default100MiB
per pod is a provisional budget, not a measured capacity. fsync may still block on
unhealthy storage. Shared ReadWriteOnce storage assumes the single-node demo cluster.

Cache entries retain original evidence and seed participates in identity. Hits record
original provenance without inventing a model call. Evaluation requests bypass cache
via X-Rahbar-Cache:bypass instead of FLUSHALL. Replay validates canonical SHA256 of
all exact message arrays using sorted-key UTF8 JSON with compact separators. Summaries
use UTC half-open windows, observed stage samples, nearest-rank percentiles and
explicit empty denominators. Stub execution is marked and is not LLM evidence.

The judge uses sanitized request-time context instead of current Chroma contents.
Suite preflight rejects incomplete golden data before service initialization; real
human labels cannot be synthesized to bypass this. API and suite seeds must agree.
Independent corpus_sha256 excludes chunk configuration/cache identity, enabling a
controlled chunking comparison. Gate provenance requires the same corpus, golden,
pairs, seed, embedding artifact, judge and query configuration; module/component/
end-to-end measurements and finite bounded thresholds are mandatory. Data drift is
not a C1 baseline/candidate comparison. Baselines require explicit creation and pass
absolute gates before an exclusive write; candidates never bootstrap themselves.

Release receipts bind result/baseline/decision hashes, completed Job UID, immutable
ConfigMap content, candidate pod template and current index generation/fingerprint.
Stale gate annotations cannot approve changed content. Promotion suspends the weekly
writer, refuses active ingestion Jobs, freezes the previous configuration for undo,
rolls the API then synchronizes the scheduled writer image/config. Failure leaves the
writer suspended. release.py undo performs Kubernetes undo plus reconciliation; raw
kubectl undo requires explicit reconcile --resume before scheduled ingestion resumes.
No force-gate bypass exists. Evaluation uses the API source-SHA-matched fourth image.

CI checks dev2/feature branches, four images and standalone manifests. Scan gates
remain enabled, including the pre-existing UI failure. Full cluster/evaluation/release
proof is Phase3; fake tests and schema validation do not establish live behavior.
