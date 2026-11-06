# ADR 0001: One writer, staged publication, API readers

Status: Accepted for Day 1, 5 November 2026.

## Context
Three API replicas share a remote Chroma server and its persistent volume.
Indexing on API startup would race three writers, repeat OCR/embedding on
every restart, and couple readiness to minutes of ingestion. Reindexing must
not require rebuilding the API, and readers must not see a half-built index.

## Decision
Only the indexer Job writes document collections. The weekly CronJob uses
the same image, command and arguments. Both mount an indexer-only lock PVC;
`flock` on the same persistent inode covers manual Jobs as well as scheduled
runs. A process crash releases the kernel lock; do not unlink the lock file.
CronJob `Forbid` is useful but is not sufficient to serialize manual Jobs.

Build a uniquely named cosine collection in batches. Validate its complete
count and dimensionality before upserting one `active` record in the logical
collection's control collection. That record includes collection name, model,
dimension, generation and content fingerprint. Readers capture one published
generation per request. Keep old generations for in-flight readers; garbage
collection is an explicit future maintenance operation, never API startup.
Publication is a single-record replacement, not a cross-collection transaction.
The single writer lock is essential. An interrupted staging run leaves an
unpublished collection, rather than deleting the previously published index.

The future Redis cache must namespace entries by index generation and verify
the current generation before hits. Thus reindexing invalidates old answers
without granting the indexer network access to Redis. The API only reads the
document/control collections; writing its separate Redis cache is permitted.

## Options considered
Delete/recreate the active collection: simple, but violates continuous serving.
In-place upserts: readers can see mixed generations and deleted chunks linger.
Kubernetes Lease: adds API credentials/RBAC to a workload that otherwise needs
none. A shared filesystem lock fits this single-node Minikube assignment.

## Consequences and verification
Stable chunk IDs are independent of the random collection generation. Failure
tests prove no publication after failed writes. A lock PVC is required for
every writer; omitting the mount invalidates serialization. This is a
single-node RWO deployment, not a multi-zone distributed-lock design.
Day 1 dummy bootstrap intentionally retains the starter's direct dummy
collection. Real publication uses the control pointer; the two modes must not
be confused. Cache integration and concurrent-request cutover evidence remain
Day 2 work. Weekly scheduling is suspended during dummy bootstrap.
