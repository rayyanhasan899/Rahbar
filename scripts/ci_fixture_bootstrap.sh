#!/usr/bin/env bash
set -euo pipefail
# ConfigMap delivery is safe for these owned, tiny CI fixtures only.
kubectl apply -k k8s/overlays/dev
kubectl -n rahbar create configmap fixture-corpus \
  --from-file=eval/fixtures/academic-rules-2023.md \
  --from-file=eval/fixtures/academic-rules-2026.md \
  --from-file=eval/fixtures/fees-2026.md --dry-run=client -o yaml | kubectl apply -f -
kubectl -n rahbar rollout status statefulset/chroma --timeout=240s
kubectl -n rahbar rollout status deployment/redis --timeout=180s
kubectl -n rahbar wait --for=condition=complete job/indexer --timeout=240s
kubectl -n rahbar rollout status deployment/api --timeout=180s
kubectl -n rahbar rollout status deployment/ui --timeout=180s
kubectl -n rahbar port-forward service/api 18000:8000 > /tmp/rahbar-ci-forward.log 2>&1 &
forward=$!
trap 'kill "$forward" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18000/readyz; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:18000/healthz
curl -fsS http://127.0.0.1:18000/api/ask -H 'Content-Type: application/json' \
  -d '{"question":"Show the stub contract"}'
