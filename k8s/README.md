# Kubernetes manifests

| Path | What |
|---|---|
| `base/` | The pipeline: API, Chroma StatefulSet + PVC, Redis, UI, Ingress, NetworkPolicies (including the eval and candidate rules), ingestion Job and weekly CronJob |
| `overlays/dev`, `overlays/prod` | Kustomize overlays used by `scripts/deploy_local.py` and CI |
| `eval-job.yaml` | Part B suite + Part C gate as a Job (Part F2) |
| `eval/` | the `eval-results` PVC, the `rahbar-gate` ConfigMap, a results shell Pod |
| `candidate/` | `api-candidate` Deployment and Service; `configmap-<name>.yaml` files written by `scripts/release.py` for each candidate |

Part A adds `base/datalake-data.yaml` and the separate ingestion/inspection objects
under `jobs/`. Part D trace persistence is Phase 2 work.

## Fresh cluster (Moez's laptop)

```bash
make cluster MINIKUBE_MEMORY=6144 MINIKUBE_CPUS=4
TAG=$(git rev-parse HEAD)
make images TAG="$TAG"                       # api, indexer, ui and rahbar-eval:dev
MODEL_IP=192.168.65.254                      # check: minikube ssh -- getent hosts host.minikube.internal
python scripts/deploy_local.py --tag "$TAG" --provider-cidr "$MODEL_IP/32" --ollama "http://$MODEL_IP:11434"
kubectl apply -f k8s/eval/eval-results.yaml -f k8s/eval/gate-configmap.yaml
```

## Verified ingestion lifecycle (Part A, ingestion F1/F2)

Implementation/limitations: [ADR 0005](../docs/adr/0005-verified-incremental-publication.md).
These are run-host instructions, not a claim that the blocked laptop executed them.
Use the existing approved Python3.12 environment and a working cluster/model host.
First fetch/verify the real documents (`python corpus/fetch.py`) and deploy using the
fresh-cluster order above. New manifests provision the persistent `datalake-data`
claim. Existing clusters need that claim before running the updated indexer image.
No API indexing occurs at startup. Never transfer a corpus concurrently with a writer.

Generate and transfer the owned controls; do not overwrite `/corpus/_index.json`:

```bash
python corpus/generate_batch_b.py
export IMAGE_TAG=$(git rev-parse HEAD)       # same SHA built and loaded on the node
python scripts/corpus_transfer.py --source corpus/batch-a --dest batch-a
python scripts/corpus_transfer.py --source corpus/batch-b --dest batch-b
mkdir -p .venv/a3-phase1
```

For safe initial demonstrations use collection `a3-lifecycle`, separate from the live
real corpus. The following creates a Job from the already deployed/tagged CronJob;
it does not edit the API, CronJob or shared ConfigMap. Use a fresh Job name per run:

```bash
kubectl -n rahbar create job --from=cronjob/reindex a3-ingest-a --dry-run=client -o json > .venv/a3-phase1/ingest-a.json
kubectl set env --local -f .venv/a3-phase1/ingest-a.json CHROMA_COLLECTION=a3-lifecycle INCOMING_DIRS=/corpus/batch-a -o json | kubectl create -f -
kubectl -n rahbar wait --for=condition=complete job/a3-ingest-a --timeout=1800s
kubectl -n rahbar logs job/a3-ingest-a > .venv/a3-phase1/ingest-a.log
# Re-run A using a new Job name: reports must show ZERO embeddings and same generation.
kubectl -n rahbar create job --from=cronjob/reindex a3-ingest-b --dry-run=client -o json > .venv/a3-phase1/ingest-b.json
kubectl set env --local -f .venv/a3-phase1/ingest-b.json CHROMA_COLLECTION=a3-lifecycle INCOMING_DIRS=/corpus/batch-a,/corpus/batch-b -o json | kubectl create -f -
kubectl -n rahbar wait --for=condition=complete job/a3-ingest-b --timeout=1800s
kubectl -n rahbar logs job/a3-ingest-b > .venv/a3-phase1/ingest-b.log
```

Before adding any input scope it must exist. All configured roots are authoritative
for deletion within that scope; an omitted root is preserved, not treated as empty.
To test real-corpus integration later, use `/corpus,/corpus/batch-a,/corpus/batch-b`
with a reviewed collection/config. The fictional collection alone is not the required
real corpus. Jobs report four checks per document and persistent quarantine reasons.
Choose the real near-duplicate threshold using measured scores, not fake-test vectors.

Prepare standalone objects with the exact built image and collection. This writes
only ignored local renderings and leaves templates untouched:

```bash
export INDEXER_IMAGE="rahbar-indexer:$IMAGE_TAG" # include registry if actually pushed there
python - <<'PY'
import json, os
from pathlib import Path
import yaml
for name in ('verify-only-job', 'rollback-job', 'datalake-inspect'):
    obj = yaml.safe_load(Path('k8s/jobs/' + name + '.yaml').read_text())
    spec = obj['spec'] if obj['kind'] == 'Pod' else obj['spec']['template']['spec']
    for container in spec['containers'] + spec.get('initContainers', []):
        container['image'] = os.environ['INDEXER_IMAGE']
        container['env'] = [{'name': 'CHROMA_COLLECTION', 'value': 'a3-lifecycle'},
                            {'name': 'INCOMING_DIRS', 'value': '/corpus/batch-a,/corpus/batch-b'}]
    if name == 'rollback-job':
        spec['containers'][0]['args'] = ['--doc-id', 'a3-demo-rules', '--version', '2026']
    Path('.venv/a3-phase1/' + name + '.json').write_text(json.dumps(obj))
PY
kubectl create -f .venv/a3-phase1/verify-only-job.json
kubectl create -f .venv/a3-phase1/datalake-inspect.json
kubectl -n rahbar wait --for=condition=ready pod/datalake-inspect --timeout=180s
kubectl -n rahbar exec datalake-inspect -- python -m pipeline.counts
kubectl create -f .venv/a3-phase1/rollback-job.json
```

Capture the generated Job names, wait for completion and collect logs. For unpin,
change only the ignored rollback rendering's args to `['--unpin','a3-demo-rules']`,
create a new generated Job, wait, then count again. All ingestion/rollback Jobs use
`INDEX_LOCK_PATH=/locks/index.lock`; read the actual ConfigMap value before running.
Inspect reports/current/archive/quarantine on the read-only inspection Pod and copy
them to an evidence folder (`kubectl cp ...`). Its data-lake mount is read-only;
it does not grant the indexer Redis access. Delete only that temporary inspection Pod
after collecting evidence. Do not delete PVCs, old snapshots or the live cluster.

`pipeline.counts` exits nonzero on count/ID/provenance disagreement. Its zero-orphan
claim is about the published collection, with archived rows explicitly counted.
Retired snapshots are retained recovery history and consume space. After a failure,
rerun the same compatible ingestion Job under a new name; the durable pointer revision
drives recovery. Do not edit `ledger.json` or manually repoint Chroma to hide an error.

A2 default retrieval excludes superseded/archived content while explicit historical
queries retain their established behavior. CO-05/06 still require partner review;
Phase 1 did not change the query API or old golden labels. Query-time traces and
actual injection-defense proof belong to later authorized phases.

## Evaluation Job (Part F2)

```bash
kubectl -n rahbar exec deploy/redis -- redis-cli FLUSHALL
kubectl -n rahbar delete job eval --ignore-not-found
kubectl apply -f k8s/eval-job.yaml
kubectl -n rahbar wait --for=condition=complete job/eval --timeout=5400s; kubectl -n rahbar logs job/eval
```

The first run on an empty `eval-results` volume is saved as `latest-baseline.json`.
The Job's exit status is the gate's. To show that a threshold change alters the
outcome without a rebuild: `kubectl -n rahbar edit configmap rahbar-gate`, then delete
and apply the Job again.

Copy the results into the repository:

```bash
kubectl apply -f k8s/eval/results-shell.yaml
kubectl -n rahbar wait --for=condition=ready pod/eval-results-shell
kubectl -n rahbar cp eval-results-shell:/results eval/results/cluster
kubectl -n rahbar delete pod eval-results-shell
```

## Candidate and release (Part C3, F3)

```bash
# candidate: own ConfigMap, collection, ingestion Job, Deployment, Service and eval Job
python scripts/release.py candidate --name rahbar-cand --chunk-size <n> --chunk-overlap <m>
# only if its gate passed:
python scripts/release.py promote --name rahbar-cand
# bad release demo, then reverse it
python scripts/release.py candidate --name rahbar-bad --chunk-size 60 --chunk-overlap 0   # gate fails
python scripts/release.py promote --name rahbar-bad --force
kubectl -n rahbar rollout undo deployment/api
kubectl -n rahbar rollout status deployment/api
kubectl -n rahbar rollout history deployment/api
```

The live Deployment rolls with `maxUnavailable: 0` and `maxSurge: 1`. Promotion sets
`CHROMA_COLLECTION` on the Deployment, so `rollout undo` brings the previous collection
back; the next trace shows it.

## Who carries what (release side)

| Object | RAGOps responsibility |
|---|---|
| Job `eval` | offline testing at three levels, release gate; fails when the gate fails |
| ConfigMap `rahbar-gate` | gate thresholds, changed without rebuilding |
| PVC `eval-results` | results and the baseline across Jobs |
| Deployment and Service `api-candidate`, ConfigMap `rahbar-config-candidate` | the candidate pipeline beside the live one (staging) |
| Deployment `api` rolling update | controlled release and rollback (`rollout status`, `rollout undo`) |
