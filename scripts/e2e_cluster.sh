#!/usr/bin/env bash
set -euo pipefail
# Requires an existing kind cluster with Calico. Images are loaded by CI or pulled
# by CD using the actual main SHA. Provider is outside the application namespace.
: "${IMAGE_TAG:?set the exact tested commit SHA}"
REGISTRY=${REGISTRY:-}
docker run -d --name rahbar-model --network kind ollama/ollama:0.6.5
provider_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' rahbar-model)
for i in $(seq 1 60); do docker exec rahbar-model ollama list && break; sleep 2; done
docker exec rahbar-model ollama pull nomic-embed-text
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.3/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=240s
python scripts/render_stack.py --fixture --tag "$IMAGE_TAG" --registry "$REGISTRY" \
  --ollama "http://$provider_ip:11434" --provider-cidr "$provider_ip/32" --out /tmp/stack.json
python - <<'PY'
import json
stack=json.load(open('/tmp/stack.json'))
deferred={'Deployment','Job','HorizontalPodAutoscaler'}
deps=[o for o in stack['items'] if o['kind'] not in deferred or o['metadata']['name']=='redis']
json.dump(dict(apiVersion='v1',kind='List',items=deps),open('/tmp/deps.json','w'))
json.dump(dict(apiVersion='v1',kind='List',items=[o for o in stack['items'] if o['kind']=='Job']),open('/tmp/indexer.json','w'))
PY
kubectl apply -f /tmp/deps.json
kubectl -n rahbar create configmap fixture-corpus \
  --from-file=eval/fixtures/academic-rules-2023.md \
  --from-file=eval/fixtures/academic-rules-2026.md \
  --from-file=eval/fixtures/fees-2026.md
kubectl -n rahbar rollout status statefulset/chroma --timeout=240s
kubectl -n rahbar rollout status deployment/redis --timeout=180s
kubectl apply -f /tmp/indexer.json
kubectl -n rahbar wait --for=condition=complete job/indexer --timeout=600s
kubectl -n rahbar logs job/indexer > /tmp/indexer.log
kubectl apply -f /tmp/stack.json
kubectl -n rahbar rollout status deployment/api --timeout=300s
kubectl -n rahbar rollout status deployment/ui --timeout=180s
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80 > /tmp/ingress-forward.log 2>&1 &
forward=$!
trap 'kill "$forward" 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -fsS -H 'Host: rahbar.local' http://127.0.0.1:18080/ && break; sleep 2; done
# Rollout readiness precedes the asynchronous Ingress endpoint update.
for i in $(seq 1 30); do
  status=$(curl -sS -o /tmp/ingress-smoke.json -w '%{http_code}' -H 'Host: rahbar.local' \
    -H 'Content-Type: application/json' -d '{"question":"When is academic warning issued?"}' \
    http://127.0.0.1:18080/api/ask || true)
  if [ "$status" = 200 ]; then break; fi
  sleep 2
done
test "$status" = 200
python eval/run_eval.py --api http://127.0.0.1:18080 --host rahbar.local \
  --golden eval/fixtures/golden.fixture.yaml --baseline eval/fixtures/baseline.json \
  --out /tmp/fixture-results.json
python - <<'PY'
import json
rows=json.load(open('/tmp/fixture-results.json'))['rows']
for row in rows:
    if row['id'] in ('f03','f06'):
        assert 'attendance is optional' not in row['response']['answer'].lower(), row
PY
kubectl -n rahbar get deployment api ui -o json > /tmp/deployed-images.json
