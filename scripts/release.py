#!/usr/bin/env python3
"""Candidate evaluation and coherent reader/writer release (A3 C3/F3).

Use `candidate`, then `promote`; `undo` reverses the API revision and reconciles the
scheduled writer. After a raw kubectl rollout undo, run `reconcile --resume` before
allowing the CronJob to run. These operations do not execute ingestion on API startup.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NS = "rahbar"
CONFIG_PREFIX = "rahbar-cfg-"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def kubectl(*args: str, stdin: str | None = None, check: bool = True) -> str:
    result = subprocess.run(["kubectl", "-n", NS, *args], input=stdin, text=True,
                            capture_output=True)
    if check and result.returncode:
        raise RuntimeError("kubectl " + " ".join(args[:3]) + " failed: " + result.stderr)
    return result.stdout


def get(kind: str, name: str) -> dict:
    return json.loads(kubectl("get", kind, *([name] if name else []), "-o", "json"))


def apply(obj: dict) -> None:
    print(kubectl("apply", "-f", "-", stdin=json.dumps(obj)).strip())


def patch(kind: str, name: str, value: dict) -> None:
    kubectl("patch", kind, name, "--type=merge", "-p", json.dumps(value))


def config_for(pod: dict) -> dict:
    """Read effective pipeline configuration, including existing explicit overrides."""
    container = pod["containers"][0]
    configs = [get("configmap", r["configMapRef"]["name"])
               for r in container.get("envFrom", []) if "configMapRef" in r]
    configs = [c for c in configs if "CHROMA_COLLECTION" in c.get("data", {})]
    if len(configs) != 1:
        raise ValueError("expected exactly one pipeline ConfigMap")
    config = copy.deepcopy(configs[0])
    for var in container.get("env", []):
        if var["name"] in config["data"]:
            if "value" not in var:
                raise ValueError("pipeline overrides must have explicit non-secret values")
            config["data"][var["name"]] = var["value"]
    return config


def immutable_config(data: dict) -> dict:
    return {"apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
            "metadata": {"name": CONFIG_PREFIX + digest(data)[:20], "namespace": NS},
            "data": data}


def use_config(pod: dict, config: dict) -> None:
    data, name = config["data"], config["metadata"]["name"]
    for container in pod.get("containers", []) + pod.get("initContainers", []):
        for ref in container.get("envFrom", []):
            old = ref.get("configMapRef", {}).get("name", "")
            if old.startswith(CONFIG_PREFIX) or old in ("rahbar-config", "rahbar-config-candidate"):
                ref["configMapRef"]["name"] = name
        # A previous `kubectl set env` must not mask the selected versioned config.
        container["env"] = [v for v in container.get("env", []) if v["name"] not in data]


def candidate_config(name: str, chunk_size: int, overlap: int) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,28}", name):
        raise ValueError("candidate collection must be 2-29 safe lowercase characters")
    if chunk_size < 2 or not 0 <= overlap < chunk_size:
        raise ValueError("chunk size/overlap must satisfy size>=2, 0<=overlap<size")
    live = config_for(get("deployment", "api")["spec"]["template"]["spec"])["data"]
    if name == live["CHROMA_COLLECTION"]:
        raise ValueError("candidate must have a different collection from live")
    config = immutable_config({**live, "CHROMA_COLLECTION": name,
                               "CHUNK_SIZE": str(chunk_size), "CHUNK_OVERLAP": str(overlap)})
    out = ROOT / "k8s/candidate" / ("configmap-" + name + ".yaml")
    out.write_text("# Immutable pipeline version generated from the selected live config.\n"
                   + yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config


def wait_job(name: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = get("job", name).get("status", {})
        conditions = status.get("conditions", [])
        if status.get("succeeded"):
            return True
        if any(c.get("type") == "Failed" and c.get("status") == "True" for c in conditions):
            return False
        time.sleep(10)
    raise RuntimeError("timed out waiting for job " + name)


def ingest(name: str, config: dict) -> str:
    spec = copy.deepcopy(get("cronjob", "reindex")["spec"]["jobTemplate"]["spec"])
    use_config(spec["template"]["spec"], config)
    image = spec["template"]["spec"]["containers"][0]["image"]
    job_name = f"ingest-{name}-{time.time_ns()}"[-63:]
    apply({"apiVersion": "batch/v1", "kind": "Job",
           "metadata": {"name": job_name, "namespace": NS}, "spec": spec})
    if not wait_job(job_name, 3600):
        raise RuntimeError("candidate ingestion failed: " + job_name)
    return image


def start_api(name: str, config: dict) -> None:
    live = get("deployment", "api")["spec"]["template"]["spec"]
    docs = yaml.safe_load_all((ROOT / "k8s/candidate/api-candidate.yaml").read_text())
    for doc in docs:
        if doc["kind"] == "Deployment":
            doc["spec"]["template"]["spec"]["containers"][0]["image"] = live["containers"][0]["image"]
            use_config(doc["spec"]["template"]["spec"], config)
            doc["metadata"].setdefault("annotations", {}).update({
                "rahbar/gate": "pending", "rahbar/collection": name, "rahbar/receipt": ""})
        apply(doc)
    kubectl("rollout", "status", "deployment/api-candidate", "--timeout=600s")


def evaluate(name: str, config: dict) -> tuple[bool, dict, dict]:
    job = yaml.safe_load((ROOT / "k8s/eval-job.yaml").read_text())
    job["metadata"]["name"] = f"eval-{name}-{time.time_ns()}"[-63:]
    pod = job["spec"]["template"]["spec"]
    use_config(pod, config)
    container = pod["containers"][0]
    api_image = get("deployment", "api-candidate")["spec"]["template"]["spec"]["containers"][0]["image"]
    repository, separator, tag = api_image.rpartition(":")
    if not separator or not re.fullmatch(r"[a-f0-9]{40,64}", tag):
        raise ValueError("candidate evaluation requires a source-SHA API image tag")
    registry = repository.rsplit("/", 1)[0] + "/" if "/" in repository else ""
    container["image"] = registry + "rahbar-eval:" + tag
    values = {"API_URL": "http://api-candidate:8000", "LABEL": name,
              "RELEASE_CONFIG_SHA256": digest(config["data"])}
    container["env"] = [v for v in container["env"] if v["name"] not in values]
    container["env"] += [{"name": k, "value": v} for k, v in values.items()]
    apply(job)
    passed = wait_job(job["metadata"]["name"], 5400)
    logs = kubectl("logs", "job/" + job["metadata"]["name"])
    receipts = [json.loads(line.removeprefix("RAHBAR_GATE_RECEIPT=")) for line in logs.splitlines()
                if line.startswith("RAHBAR_GATE_RECEIPT=")]
    if len(receipts) != 1 or receipts[0].get("passed") is not passed:
        raise ValueError("completed evaluation must emit exactly one matching gate receipt")
    return passed, receipts[0], get("job", job["metadata"]["name"])


def index_state(deployment: str) -> dict:
    # Read-only REST probe from an existing API pod; no credentials or full chunks logged.
    code = '''import json,httpx
from app.config import get_settings
s=get_settings()
r=f"http://{s.chroma_host}:{s.chroma_port}/api/v2/tenants/default_tenant/databases/default_database/collections"
with httpx.Client(timeout=10) as c:
    x=c.get(r+"/"+s.collection+"-control"); x.raise_for_status()
    y=c.post(r+"/"+x.json()["id"]+"/get",json={"ids":["active"],"include":["metadatas"]}); y.raise_for_status()
    print(json.dumps({"name":s.collection,**y.json()["metadatas"][0]}))
'''
    return json.loads(kubectl("exec", "deployment/" + deployment, "--", "python", "-c", code))


def verify_index(receipt: dict, deployment: str) -> None:
    provenance = receipt["provenance"]
    expected = provenance.get("index", {})
    current = index_state(deployment)
    for key in ("name", "active_collection", "generation", "fingerprint"):
        if not expected.get(key) or current.get(key) != expected[key]:
            raise ValueError("candidate index changed or missing evaluated provenance: " + key)
    for field, key in (("corpus_sha256", "corpus_sha256"), ("embedding_digest", "embed_model_digest")):
        if not provenance.get(field) or provenance[field] != current.get(key):
            raise ValueError("candidate provenance mismatch: " + field)


def candidate(args: argparse.Namespace) -> int:
    config = candidate_config(args.name, args.chunk_size, args.chunk_overlap)
    apply(config)
    image = ingest(args.name, config)
    start_api(args.name, config)
    passed, receipt, job = evaluate(args.name, config)
    deployment = get("deployment", "api-candidate")
    binding = {"receipt": receipt, "config": config["metadata"]["name"],
               "config_sha256": digest(config["data"]),
               "template_sha256": digest(deployment["spec"]["template"]),
               "job_name": job["metadata"]["name"], "job_uid": job["metadata"]["uid"],
               "indexer_image": image}
    patch("deployment", "api-candidate", {"metadata": {"annotations": {
        "rahbar/gate": "passed" if passed else "failed", "rahbar/collection": args.name,
        "rahbar/receipt": json.dumps(binding, sort_keys=True)}}})
    print("GATE", "PASSED" if passed else "FAILED", "for", args.name)
    return 0 if passed else 1


def validated_candidate(name: str) -> tuple[dict, dict]:
    deployment = get("deployment", "api-candidate")
    notes = deployment["metadata"].get("annotations", {})
    if notes.get("rahbar/collection") != name:
        raise ValueError("candidate collection differs from requested release")
    binding = json.loads(notes.get("rahbar/receipt") or "{}")
    receipt = binding.get("receipt", {})
    if notes.get("rahbar/gate") != "passed" or receipt.get("passed") is not True:
        raise ValueError("candidate has no passed evaluated gate")
    if digest(deployment["spec"]["template"]) != binding.get("template_sha256"):
        raise ValueError("candidate pod template changed after evaluation")
    config = get("configmap", binding["config"])
    sha = digest(config["data"])
    if (config.get("immutable") is not True or sha != binding["config_sha256"]
            or receipt["provenance"].get("release_config_sha256") != sha
            or config["data"]["CHROMA_COLLECTION"] != name):
        raise ValueError("candidate configuration changed after evaluation")
    job = get("job", binding["job_name"])
    if job["metadata"]["uid"] != binding["job_uid"] or not job.get("status", {}).get("succeeded"):
        raise ValueError("evaluated Job no longer matches completed receipt")
    for field in ("candidate_sha256", "baseline_sha256", "decision_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get(field, ""))):
            raise ValueError("missing immutable evaluation hash: " + field)
    verify_index(receipt, "api-candidate")
    return deployment, binding


def suspend_writer() -> bool:
    cron = get("cronjob", "reindex")
    previous = bool(cron["spec"].get("suspend", False))
    patch("cronjob", "reindex", {"metadata": {"annotations": {
        "rahbar/previous-suspend": str(previous).lower()}}, "spec": {"suspend": True}})
    # An already running Job is not stopped by CronJob suspend. Refuse configuration
    # changes until active indexer Jobs finish; never delete them or hide contention.
    active = get("jobs", "").get("items", [])
    if any(j.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {}).get(
            "app") == "indexer" and j.get("status", {}).get("active", 0) for j in active):
        raise ValueError("writer Job still active; CronJob kept suspended; finish it then reconcile")
    return previous


def rollout() -> None:
    kubectl("rollout", "status", "deployment/api", "--timeout=600s")


def reconcile(resume: bool = False) -> int:
    api = get("deployment", "api")
    config = config_for(api["spec"]["template"]["spec"])
    if config.get("immutable") is not True:
        raise ValueError("live API must select a versioned immutable pipeline config")
    cron = get("cronjob", "reindex")
    spec = copy.deepcopy(cron["spec"]["jobTemplate"]["spec"])
    use_config(spec["template"]["spec"], config)
    image = api["spec"]["template"]["metadata"].get("annotations", {}).get("rahbar/indexer-image")
    if not image:
        raise ValueError("live API revision lacks ingestion image provenance")
    for container in spec["template"]["spec"].get("containers", []) + spec["template"]["spec"].get("initContainers", []):
        container["image"] = image
    value = {"spec": {"jobTemplate": {"spec": spec}}}
    if resume:
        previous = cron.get("metadata", {}).get("annotations", {}).get("rahbar/previous-suspend")
        if previous not in ("true", "false"):
            raise ValueError("no recorded previous CronJob suspension state")
        value["spec"]["suspend"] = previous == "true"
    patch("cronjob", "reindex", value)
    return 0


def promote(args: argparse.Namespace) -> int:
    deployment, binding = validated_candidate(args.name)  # No live mutation on failed gate.
    suspend_writer()
    live = get("deployment", "api")
    template = copy.deepcopy(live["spec"]["template"])
    # Freeze the old revision first so kubectl undo restores configuration bytes,
    # not a mutable ConfigMap name. Keep its matching ingestion image in the revision.
    old_config = immutable_config(config_for(template["spec"])["data"])
    apply(old_config)
    use_config(template["spec"], old_config)
    cron = get("cronjob", "reindex")
    old_image = cron["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]["image"]
    template.setdefault("metadata", {}).setdefault("annotations", {})["rahbar/indexer-image"] = old_image
    if template != live["spec"]["template"]:
        patch("deployment", "api", {"spec": {"template": template}})
        rollout()
    config = get("configmap", binding["config"])
    use_config(template["spec"], config)
    template["spec"]["containers"][0]["image"] = deployment["spec"]["template"]["spec"]["containers"][0]["image"]
    template["metadata"]["annotations"].update({"rahbar/indexer-image": binding["indexer_image"],
                                              "rahbar/evaluated-generation": binding["receipt"]["provenance"]["index"]["generation"]})
    patch("deployment", "api", {"metadata": {"annotations": {
        "kubernetes.io/change-cause": "evaluated release " + args.name}}, "spec": {"template": template}})
    rollout()
    verify_index(binding["receipt"], "api")
    reconcile(resume=True)
    print("Released", args.name, "with the matching scheduled writer. Reverse with release.py undo.")
    return 0


def undo() -> int:
    suspend_writer()
    kubectl("rollout", "undo", "deployment/api")
    rollout()
    reconcile(resume=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("candidate")
    c.add_argument("--name", required=True)
    c.add_argument("--chunk-size", type=int, required=True)
    c.add_argument("--chunk-overlap", type=int, required=True)
    p = sub.add_parser("promote")
    p.add_argument("--name", required=True)
    sub.add_parser("undo")
    r = sub.add_parser("reconcile")
    r.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "candidate":
            return candidate(args)
        if args.command == "promote":
            return promote(args)
        return undo() if args.command == "undo" else reconcile(args.resume)
    except (RuntimeError, ValueError, KeyError) as exc:
        print("Release stopped:", str(exc), file=sys.stderr)
        print("If the writer was suspended, repair/review and use release.py reconcile --resume.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
