# Kubernetes manifests

| Path | What |
|---|---|
| `base/` | The pipeline: API, Chroma StatefulSet + PVC, Redis, UI, Ingress, NetworkPolicies (including the eval and candidate rules), ingestion Job and weekly CronJob |
| `overlays/dev`, `overlays/prod` | Kustomize overlays used by `scripts/deploy_local.py` and CI |
| `eval-job.yaml` | Part B suite + Part C gate as a Job (Part F2) |
| `eval/` | the `eval-results` PVC, the `rahbar-gate` ConfigMap, a results shell Pod |
| `candidate/` | `api-candidate` Deployment and Service; `configmap-<name>.yaml` files written by `scripts/release.py` for each candidate |

Part A and D objects (data lake, traces, rollback Job) are added with Rayyan's work.

## Fresh cluster (Moez's laptop)

```bash
make cluster MINIKUBE_MEMORY=6144 MINIKUBE_CPUS=4
TAG=$(git rev-parse HEAD)
make images TAG="$TAG"                       # api, indexer, ui and rahbar-eval:dev
MODEL_IP=192.168.65.254                      # check: minikube ssh -- getent hosts host.minikube.internal
python scripts/deploy_local.py --tag "$TAG" --provider-cidr "$MODEL_IP/32" --ollama "http://$MODEL_IP:11434"
kubectl apply -f k8s/eval/eval-results.yaml -f k8s/eval/gate-configmap.yaml
```

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
