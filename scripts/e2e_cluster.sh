#!/usr/bin/env bash
set -euo pipefail
# Requires an existing kind cluster with Calico. Images are loaded by CI or pulled
# by CD using the actual main SHA. Provider is outside the application namespace.
: "${IMAGE_TAG:?set the exact tested commit SHA}"
REGISTRY=${REGISTRY:-}
MODE=${CORPUS_MODE:-fixture}
docker run -d --name rahbar-model --network kind ollama/ollama:0.6.5
provider_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' rahbar-model)
for i in $(seq 1 60); do docker exec rahbar-model ollama list && break; sleep 2; done
docker exec rahbar-model ollama pull nomic-embed-text
if [ "$MODE" = real ]; then docker exec rahbar-model ollama pull llama3.2:3b; fi
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.3/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=240s
kubectl -n ingress-nginx wait --for=condition=complete job/ingress-nginx-admission-create --timeout=180s
kubectl -n ingress-nginx wait --for=condition=complete job/ingress-nginx-admission-patch --timeout=180s
fixture_args=()
if [ "$MODE" = fixture ]; then fixture_args=(--fixture); fi
python scripts/render_stack.py "${fixture_args[@]}" --tag "$IMAGE_TAG" --registry "$REGISTRY" \
  --ollama "http://$provider_ip:11434" --provider-cidr "$provider_ip/32" --out /tmp/stack.json
python - <<'PY'
import json
stack=json.load(open('/tmp/stack.json'))
deferred={'Deployment','Job','CronJob','HorizontalPodAutoscaler'}
deps=[o for o in stack['items'] if o['kind'] not in deferred or o['metadata']['name']=='redis']
json.dump(dict(apiVersion='v1',kind='List',items=deps),open('/tmp/deps.json','w'))
json.dump(dict(apiVersion='v1',kind='List',items=[o for o in stack['items'] if o['kind']=='Job']),open('/tmp/indexer.json','w'))
PY
dependencies_ready=false
for attempt in $(seq 1 10); do
  if kubectl apply -f /tmp/deps.json; then dependencies_ready=true; break; fi
  sleep 3
done
"$dependencies_ready"
if [ "$MODE" = fixture ]; then
kubectl -n rahbar create configmap fixture-corpus \
  --from-file=eval/fixtures/academic-rules-2023.md \
  --from-file=eval/fixtures/academic-rules-2026.md \
  --from-file=eval/fixtures/fees-2026.md
else
  cp corpus/MANIFEST.md /tmp/corpus-pinned-manifest.md
  python corpus/fetch.py
  python corpus/fetch.py --verify
  python - <<'PY'
import pathlib,re
pinned=re.findall(r'\b[a-f0-9]{64}\b',pathlib.Path('/tmp/corpus-pinned-manifest.md').read_text())
actual=re.findall(r'\b[a-f0-9]{64}\b',pathlib.Path('corpus/MANIFEST.md').read_text())
assert sorted(pinned)==sorted(actual), 'live source bytes differ from committed corpus manifest'
PY
  python scripts/corpus_transfer.py
fi
kubectl -n rahbar rollout status statefulset/chroma --timeout=240s
kubectl -n rahbar rollout status deployment/redis --timeout=180s
if [ "$MODE" = real ]; then
  (while true; do date -u +%FT%TZ; kubectl -n rahbar top pod -l app=indexer --containers || true; sleep 3; done) > /tmp/indexer-top.log 2>&1 &
  monitor=$!
fi
kubectl apply -f /tmp/indexer.json
kubectl -n rahbar wait --for=condition=complete job/indexer --timeout=1800s
if [ "$MODE" = real ]; then kill "$monitor" 2>/dev/null || true; fi
kubectl -n rahbar logs job/indexer > /tmp/indexer.log
kubectl apply -f /tmp/stack.json
kubectl -n rahbar rollout status deployment/api --timeout=300s
kubectl -n rahbar rollout status deployment/ui --timeout=180s
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80 > /tmp/ingress-forward.log 2>&1 &
forward=$!
trap 'kill "$forward" 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -fsS -H 'Host: rahbar.local' http://127.0.0.1:18080/ -o /tmp/ui-smoke.html && break; sleep 2; done
# Rollout readiness precedes the asynchronous Ingress endpoint update.
for i in $(seq 1 30); do
  status=$(curl -sS -o /tmp/ingress-smoke.json -w '%{http_code}' -H 'Host: rahbar.local' \
    -H 'Content-Type: application/json' -d '{"question":"When is academic warning issued?"}' \
    http://127.0.0.1:18080/api/ask || true)
  if [ "$status" = 200 ]; then break; fi
  sleep 2
done
test "$status" = 200
if [ "$MODE" = real ]; then
  export MODEL_IP="$provider_ip"
  python scripts/real_cluster_checks.py
  exit
fi
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
