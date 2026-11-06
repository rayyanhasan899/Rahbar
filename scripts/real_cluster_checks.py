"""Controlled acceptance experiments on an ephemeral real-corpus cluster.

Never run against a shared cluster: this intentionally replaces project pods and
temporarily changes the embedding pin. Every configuration change has a finally
restoration. Evidence records failures and continues through independent checks.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import httpx

OUT = Path("/tmp/real-audit")
OUT.mkdir(exist_ok=True)
REPORT: dict = {"commit": os.environ["IMAGE_TAG"], "checks": {}}
API = "http://127.0.0.1:18080"
HEADERS = {"Host": "rahbar.local"}


def command(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(args, input=stdin, text=True, capture_output=True, timeout=1900)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)}: {result.stdout[-1500:]} {result.stderr[-1500:]}")
    return result.stdout


def k(*args: str) -> str:
    return command("kubectl", "-n", "rahbar", *args)


def j(*args: str):
    return json.loads(k(*args, "-o", "json"))


def remote(code: str) -> str:
    return k("exec", "deployment/api", "--", "python", "-c", code)


def publication() -> dict:
    return json.loads(remote("import json;from app.config import get_settings;from app.retrieval.chroma import ChromaRetriever;r=ChromaRetriever(get_settings());c,m=r.active();print(json.dumps(dict(m,count=c.count())))"))


def ask(question: str, history: list | None = None) -> httpx.Response:
    body: dict = {"question": question}
    if history is not None:
        body["history"] = history
    response = httpx.post(API + "/api/ask", headers=HEADERS, json=body, timeout=300)
    response.raise_for_status()
    return response


def save(name: str, value) -> None:
    (OUT / name).write_text(value if isinstance(value, str) else json.dumps(value, indent=2))


def check(name, function):
    started = time.time()
    try:
        evidence = function()
        REPORT["checks"][name] = {"status": "PASS", "evidence": evidence, "seconds": round(time.time() - started, 2)}
    except Exception as exc:
        REPORT["checks"][name] = {"status": "FAIL", "error": str(exc), "seconds": round(time.time() - started, 2)}
    save("report.json", REPORT)
    print(json.dumps({"check": name, **REPORT["checks"][name]}), flush=True)


def ready() -> None:
    k("wait", "--for=condition=ready", "pod", "-l", "app=api", "--timeout=300s")
    k("rollout", "status", "deployment/api", "--timeout=300s")


def network() -> dict:
    results = {}
    for label, target, port, expected in [
        ("api", "chroma", 8000, True), ("api", "redis", 6379, True),
        ("api", "host-provider", 11434, True),
        ("ui", "api", 8000, True), ("ui", "chroma", 8000, False),
    ]:
        if label == "ui":
            # Resolve DNS first; an invalid command or DNS failure is not proof of deny.
            dns = k("exec", "deployment/ui", "--", "nslookup", target)
            path = "/healthz" if target == "api" else "/api/v2/heartbeat"
            result = subprocess.run(["kubectl", "-n", "rahbar", "exec", "deployment/ui", "--", "wget", "-T", "3", "-q", "-O", "-", f"http://{target}:{port}{path}"], capture_output=True, text=True)
            if not expected:
                assert any(reason in result.stderr.lower() for reason in ("timed out", "timeout", "connection refused")), result.stderr
        else:
            host = os.environ["MODEL_IP"] if target == "host-provider" else target
            code = f"import socket;s=socket.create_connection(({host!r},{port}),timeout=3);s.close();print('connected')"
            result = subprocess.run(["kubectl", "-n", "rahbar", "exec", "deployment/api", "--", "python", "-c", code], capture_output=True, text=True)
            dns = "resolved by socket.create_connection"
        actual = result.returncode == 0
        results[f"{label}->{target}"] = {"allowed": actual, "expected": expected, "dns": dns, "output": result.stdout + result.stderr}
        if actual != expected:
            save("network.json", results)
            raise AssertionError(results)
    response = httpx.get(API + "/", headers=HEADERS)
    response.raise_for_status()
    results["Ingress->UI"] = response.status_code
    response = ask("What is the medium of instruction?")
    results["Ingress->API"] = response.status_code
    save("network.json", results)
    return results


def persistence() -> dict:
    before = publication()
    remote("import redis;from app.config import get_settings;s=get_settings();r=redis.Redis(host=s.redis_host,port=s.redis_port);r.set('rahbar:day3:persistence','survived',ex=1800)")
    k("delete", "pod/chroma-0", "--wait=true")
    k("rollout", "status", "statefulset/chroma", "--timeout=300s")
    ready()
    after = publication()
    assert before["generation"] == after["generation"] and before["count"] == after["count"]
    redis_pod = j("get", "pods", "-l", "app=redis")["items"][0]["metadata"]["name"]
    k("delete", "pod", redis_pod, "--wait=true")
    k("rollout", "status", "deployment/redis", "--timeout=300s")
    ready()
    marker = remote("import redis;from app.config import get_settings;s=get_settings();assert redis.Redis(host=s.redis_host,port=s.redis_port).get('rahbar:day3:persistence')==b'survived';print('Redis AOF marker survived')")
    pods = j("get", "pods", "-l", "app=api")["items"]
    deleted = pods[0]["metadata"]["name"]
    k("delete", "pod", deleted, "--wait=true")
    ready()
    assert all(p["metadata"]["name"] != deleted for p in j("get", "pods", "-l", "app=api")["items"])
    save("persistence.json", {"before": before, "after": after, "redis": marker, "deleted_api": deleted})
    return {"generation": after["generation"], "chunks": after["count"], "redis": marker, "deleted_api": deleted}


def pin_conflict() -> dict:
    original = j("get", "configmap", "rahbar-config")["data"]["EMBED_MODEL"]
    previous = {p["metadata"]["uid"] for p in j("get", "pods", "-l", "app=api")["items"]}
    evidence = {}
    try:
        k("patch", "configmap", "rahbar-config", "--type=merge", "-p", json.dumps({"data": {"EMBED_MODEL": "deliberately-wrong-model"}}))
        k("rollout", "restart", "deployment/api")
        for _ in range(60):
            new = [p for p in j("get", "pods", "-l", "app=api")["items"] if p["metadata"]["uid"] not in previous]
            if new:
                p = new[0]
                logs = k("logs", p["metadata"]["name"])
                if "embedding model mismatch" in logs and "deliberately-wrong-model" in logs:
                    assert not any(c.get("ready") for c in p["status"].get("containerStatuses", []))
                    evidence = {"pod": p["metadata"]["name"], "ready": False, "logs": logs}
                    save("pin-conflict.json", evidence)
                    break
            time.sleep(2)
        assert evidence, "no explicit non-ready pin conflict observed"
    finally:
        k("patch", "configmap", "rahbar-config", "--type=merge", "-p", json.dumps({"data": {"EMBED_MODEL": original}}))
        k("rollout", "undo", "deployment/api")
        ready()
    evidence["restored_publication"] = publication()
    save("pin-conflict.json", evidence)
    return {"bad_pod": evidence["pod"], "bad_ready": False, "restored_model": original}


def rollout() -> dict:
    original = j("get", "deployment", "ui")["spec"]["template"]["spec"]["containers"][0]["image"]
    context = Path(".venv/rollout-demo")
    context.mkdir(parents=True, exist_ok=True)
    context.joinpath("index.html").write_text(Path("ui/index.html").read_text().replace("RAHBAR", "RAHBAR Rollout Demo"))
    context.joinpath("Dockerfile").write_text(f"FROM {original}\nUSER root\nCOPY index.html /usr/share/nginx/html/index.html\nUSER 101:101\n")
    image = "rahbar-ui:" + os.environ["IMAGE_TAG"] + "-demo"
    command("docker", "build", "-t", image, str(context))
    command("kind", "load", "docker-image", image, "--name", os.environ["CLUSTER_NAME"])
    try:
        k("set", "image", "deployment/ui", "ui=" + image)
        k("rollout", "status", "deployment/ui", "--timeout=180s")
        for _ in range(30):
            html = httpx.get(API + "/", headers=HEADERS).text
            if "RAHBAR Rollout Demo" in html:
                break
            time.sleep(2)
        assert "RAHBAR Rollout Demo" in html
        save("rollout-visible.html", html)
    finally:
        k("rollout", "undo", "deployment/ui")
        k("rollout", "status", "deployment/ui", "--timeout=180s")
    for _ in range(30):
        html = httpx.get(API + "/", headers=HEADERS).text
        if "RAHBAR Rollout Demo" not in html:
            break
        time.sleep(2)
    assert "RAHBAR Rollout Demo" not in html
    assert j("get", "deployment", "ui")["spec"]["template"]["spec"]["containers"][0]["image"] == original
    save("rollout-restored.html", html)
    return {"original": original, "demo": image, "restored_sha256": hashlib.sha256(html.encode()).hexdigest()}


def reindex() -> dict:
    before = publication()
    warm = ask("What is the medium of instruction and examinations for most courses?")
    hit = ask("What is the medium of instruction and examinations for most courses?")
    assert hit.headers.get("X-Cache") == "hit", hit.text
    deployment = j("get", "deployment", "api")["spec"]["template"]
    name = "acceptance-reindex"
    k("create", "job", "--from=cronjob/reindex", name)
    for _ in range(90):
        result = subprocess.run(["kubectl", "-n", "rahbar", "logs", "job/" + name], capture_output=True, text=True)
        if '"msg": "writer acquired"' in result.stdout:
            break
        time.sleep(2)
    else:
        raise AssertionError("real reindex never acquired the shared writer lock")
    # A manual Job enters exactly the same writer lock while the real reindex runs.
    lock = j("get", "job", name)
    lock.pop("status", None)
    lock["metadata"] = {"name": "manual-lock-probe", "namespace": "rahbar"}
    lock["spec"].pop("selector", None)
    lock["spec"]["template"]["metadata"] = {"labels": {"app": "indexer"}}
    container = lock["spec"]["template"]["spec"]["containers"][0]
    container["command"] = ["python", "-c", "from pipeline.run import writer_lock,log;import time;time.sleep(5);\nwith writer_lock('/locks/index.lock'):log('manual probe entered writer critical section')"]
    container["args"] = []
    command("kubectl", "apply", "-f", "-", stdin=json.dumps(lock))
    probes = []
    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        response = ask("What is the medium of instruction and examinations for most courses?")
        probes.append({"time": time.time(), "status": response.status_code, "cache": response.headers.get("X-Cache")})
        if j("get", "job", name).get("status", {}).get("succeeded"):
            break
        time.sleep(3)
    k("wait", "--for=condition=complete", "job/" + name, "--timeout=60s")
    k("wait", "--for=condition=complete", "job/manual-lock-probe", "--timeout=120s")
    after = publication()
    assert before["generation"] != after["generation"]
    assert before["count"] == after["count"]
    assert deployment == j("get", "deployment", "api")["spec"]["template"]
    # A probe may already have crossed publication and filled the new namespace.
    first_after = ask("What is the medium of instruction and examinations for most courses?")
    new_hit = ask("What is the medium of instruction and examinations for most courses?")
    assert new_hit.headers.get("X-Cache") == "hit"
    assert first_after.headers.get("X-Cache") == "miss" or any(p["cache"] == "miss" for p in probes), probes
    save("reindex.json", {"before": before, "after": after, "probes": probes, "warm_cache": warm.headers.get("X-Cache"), "first_after_cache": first_after.headers.get("X-Cache"), "second_after_cache": new_hit.headers.get("X-Cache")})
    save("reindex-writer.log", k("logs", "job/" + name))
    lock_log = k("logs", "job/manual-lock-probe")
    save("manual-lock.log", lock_log)
    acquired = [json.loads(line) for line in lock_log.splitlines() if '"msg": "writer acquired"' in line]
    assert acquired and acquired[0]["wait_seconds"] >= 1, lock_log
    return {"before": before["generation"], "after": after["generation"], "successful_probes": len(probes), "deployment_unchanged": True}


def metrics() -> dict:
    snapshots = []
    with concurrent.futures.ThreadPoolExecutor() as pool:
        pending = pool.submit(ask, "And what does that require?", [{"question": "What attendance does clause 1.21 require?", "answer": "Please check the policy."}])
        for _ in range(4):
            snapshots.append({"time": time.time(), "top": k("top", "pods", "--containers"), "hpa": j("get", "hpa", "api")})
            time.sleep(5)
        response = pending.result()
    endpoints = j("get", "endpoints", "api")
    ips = [a["ip"] for subset in endpoints.get("subsets", []) for a in subset.get("addresses", [])]
    assert len(ips) >= 3, ips
    for _ in range(30):
        hpa = j("get", "hpa", "api")
        current = hpa.get("status", {}).get("currentMetrics", [])
        if any(isinstance(m.get("resource", {}).get("current", {}).get("averageUtilization"), int) for m in current):
            break
        time.sleep(5)
    else:
        raise AssertionError("HPA CPU utilization is not numeric")
    save("resources.json", {"samples": snapshots, "hpa": hpa, "endpoints": ips, "followup_response": response.json()})
    save("metrics.txt", remote("import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())"))
    return {"endpoint_ips": ips, "hpa": current}


def evaluate() -> dict:
    args = ["python", "eval/run_eval.py", "--api", API, "--host", "rahbar.local", "--out", str(OUT / "results.json")]
    if Path("eval/baseline.json").exists():
        args += ["--baseline", "eval/baseline.json"]
    else:
        args += ["--baseline", str(OUT / "baseline.json"), "--update-baseline"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=3600)
    save("evaluation.log", result.stdout + result.stderr)
    if result.returncode:
        raise AssertionError(result.stdout[-2000:] + result.stderr[-1000:])
    data = json.loads((OUT / "results.json").read_text())
    return {key: data[key] for key in ["recall_at_3", "recall_at_5", "citation_validity", "abstention_correctness", "questions"]}


def component_experiments() -> dict:
    log = OUT / "component-experiments.log"
    env = dict(os.environ, CHROMA_HOST="127.0.0.1", CHROMA_PORT="18004", CHROMA_COLLECTION="rahbar-experiment", OLLAMA_URL=f"http://{os.environ['MODEL_IP']}:11434", INDEX_LOCK_PATH="/tmp/rahbar-experiment.lock", PYTHONUNBUFFERED="1")
    with (OUT / "chroma-forward.log").open("w") as stream:
        forward = subprocess.Popen(["kubectl", "-n", "rahbar", "port-forward", "service/chroma", "18004:8000"], stdout=stream, stderr=subprocess.STDOUT)
        try:
            for _ in range(30):
                try:
                    httpx.get("http://127.0.0.1:18004/api/v2/heartbeat").raise_for_status()
                    break
                except httpx.HTTPError:
                    time.sleep(1)
            with log.open("w") as output:
                for args in [
                    ["python", "scripts/audit_corpus.py"],
                    ["python", "scripts/chunk_experiment.py", "--out", str(OUT / "chunk-experiments.json")],
                    ["python", "scripts/failure_experiments.py"],
                    ["python", "scripts/real_poison_probe.py"],
                    ["python", "scripts/cache_threshold_experiment.py"],
                ]:
                    result = subprocess.run(args, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=2400)
                    if result.returncode:
                        raise RuntimeError(f"{args} failed; see component-experiments.log")
        finally:
            forward.terminate()
            forward.wait(timeout=10)
    for source, destination in [("docs/evidence/extraction-audit.json", "extraction-audit.json"), ("eval/cache-threshold-experiment.json", "cache-threshold-experiment.json")]:
        save(destination, Path(source).read_text())
    return {"fresh_extraction": True, "measured_chunk_configurations": 3, "failure_stages": ["A", "B", "C", "E"], "real_poison_fixture": True}


def main() -> None:
    save("initial-publication.json", publication())
    check("real-golden", evaluate)
    check("network", network)
    check("persistence", persistence)
    check("embedding-pin-conflict", pin_conflict)
    check("visible-rollout-and-undo", rollout)
    check("reindex-cache-and-writer-serialization", reindex)
    check("resources-and-endpoints", metrics)
    check("real-ui-screenshot", lambda: command("python", "scripts/capture_ui.py"))
    check("component-experiments", component_experiments)
    save("final-resources.json", j("get", "pods,deployments,statefulsets,services,jobs,cronjobs,pvc,networkpolicies,hpa,endpoints,serviceaccounts,configmaps,ingresses"))
    if any(item["status"] != "PASS" for item in REPORT["checks"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
