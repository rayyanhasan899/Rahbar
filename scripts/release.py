#!/usr/bin/env python3
"""Controlled release of a pipeline change (Part C3 and F3).

    # 1. build and test a candidate: its own ConfigMap, collection, Deployment, Service
    python scripts/release.py candidate --name rahbar-cand --chunk-size 400 --chunk-overlap 50

    # 2. release it to the live API with a rolling update (only if its gate passed)
    python scripts/release.py promote --name rahbar-cand
    python scripts/release.py promote --name rahbar-bad --force   # the bad-release demo

    # 3. reverse a bad release
    kubectl -n rahbar rollout undo deployment/api && kubectl -n rahbar rollout status deployment/api

`candidate` copies the live ConfigMap with the new collection and chunking (and the
answer cache off, so the suite measures the pipeline), runs the ingestion Job from the
CronJob's own template against that ConfigMap, starts api-candidate with the live API's
image, runs the eval Job against it and records the gate result on the Deployment. It
exits 1 when the gate fails: that candidate is never rolled out.

`promote` sets CHROMA_COLLECTION on the live Deployment (maxUnavailable 0) with a
change-cause, then waits on `kubectl rollout status`.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NS = "rahbar"
CANDIDATE_CONFIG = "rahbar-config-candidate"


def kubectl(*args: str, stdin: str | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["kubectl", "-n", NS, *args], input=stdin, text=True, capture_output=True
    )
    if check and result.returncode:
        sys.exit("kubectl " + " ".join(args) + " failed:\n" + result.stderr)
    return result.stdout


def get(kind: str, name: str) -> dict:
    return json.loads(kubectl("get", kind, name, "-o", "json"))


def apply(obj: dict) -> None:
    print(kubectl("apply", "-f", "-", stdin=json.dumps(obj)).strip())


def candidate_config(name: str, chunk_size: int, overlap: int) -> dict:
    live = get("configmap", "rahbar-config")["data"]
    data = {**live, "CHROMA_COLLECTION": name, "CHUNK_SIZE": str(chunk_size),
            "CHUNK_OVERLAP": str(overlap), "CACHE_ENABLED": "false"}
    config = {"apiVersion": "v1", "kind": "ConfigMap",
              "metadata": {"name": CANDIDATE_CONFIG, "namespace": NS}, "data": data}
    out = ROOT / "k8s" / "candidate" / f"configmap-{name}.yaml"
    out.write_text(
        "# Written by scripts/release.py from the live ConfigMap; only the collection,\n"
        "# the chunking and the cache differ.\n" + yaml.safe_dump(config, sort_keys=True),
        encoding="utf-8",
    )
    print("candidate ConfigMap written:", out.relative_to(ROOT))
    return config


def use_config(pod_spec: dict, config: str) -> None:
    for container in pod_spec.get("containers", []) + pod_spec.get("initContainers", []):
        for ref in container.get("envFrom", []):
            if ref.get("configMapRef", {}).get("name") == "rahbar-config":
                ref["configMapRef"]["name"] = config


def wait_job(name: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = get("job", name).get("status", {})
        if status.get("succeeded"):
            return True
        if status.get("failed"):
            return False
        time.sleep(10)
    sys.exit("timed out waiting for job " + name)


def ingest(name: str) -> None:
    template = get("cronjob", "reindex")["spec"]["jobTemplate"]["spec"]
    spec = copy.deepcopy(template)
    use_config(spec["template"]["spec"], CANDIDATE_CONFIG)
    job_name = f"ingest-{name}-{int(time.time())}"[:63]
    apply({"apiVersion": "batch/v1", "kind": "Job",
           "metadata": {"name": job_name, "namespace": NS}, "spec": spec})
    print("waiting for", job_name)
    if not wait_job(job_name, 3600):
        sys.exit("candidate ingestion failed: kubectl -n rahbar logs job/" + job_name)


def start_api(name: str) -> None:
    live_image = get("deployment", "api")["spec"]["template"]["spec"]["containers"][0]["image"]
    docs = list(yaml.safe_load_all((ROOT / "k8s/candidate/api-candidate.yaml").read_text()))
    for doc in docs:
        if doc["kind"] == "Deployment":
            doc["spec"]["template"]["spec"]["containers"][0]["image"] = live_image
            doc["metadata"].setdefault("annotations", {})["rahbar/collection"] = name
        apply(doc)
    # A gate result from an earlier candidate must never be read as this one's.
    kubectl("annotate", "deployment/api-candidate", "--overwrite", "rahbar/gate=pending")
    kubectl("rollout", "restart", "deployment/api-candidate")  # pick up the new ConfigMap
    print(kubectl("rollout", "status", "deployment/api-candidate", "--timeout=600s").strip())


def evaluate(name: str) -> bool:
    job = yaml.safe_load((ROOT / "k8s/eval-job.yaml").read_text())
    job["metadata"]["name"] = f"eval-{name}-{int(time.time())}"[:63]
    pod = job["spec"]["template"]["spec"]
    use_config(pod, CANDIDATE_CONFIG)
    for var in pod["containers"][0]["env"]:
        if var["name"] == "API_URL":
            var["value"] = "http://api-candidate:8000"
        if var["name"] == "LABEL":
            var["value"] = name
    apply(job)
    print("waiting for", job["metadata"]["name"], "(the suite takes a while)")
    passed = wait_job(job["metadata"]["name"], 5400)
    print(kubectl("logs", "job/" + job["metadata"]["name"], "--tail=40", check=False))
    return passed


def candidate(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", args.name) or args.name == "rahbar":
        sys.exit("--name must be a new lowercase collection name, not the live one")
    apply(candidate_config(args.name, args.chunk_size, args.chunk_overlap))
    if not args.skip_ingest:
        ingest(args.name)
    start_api(args.name)
    passed = evaluate(args.name)
    kubectl("annotate", "deployment/api-candidate", "--overwrite",
            f"rahbar/gate={'passed' if passed else 'failed'}", f"rahbar/collection={args.name}")
    if passed:
        print("GATE PASSED for", args.name, "- release with: scripts/release.py promote --name",
              args.name)
        return 0
    print("GATE FAILED for", args.name, "- stopped here, the live API is unchanged")
    return 1


def promote(args: argparse.Namespace) -> int:
    notes = get("deployment", "api-candidate")["metadata"].get("annotations", {})
    gate = notes.get("rahbar/gate") if notes.get("rahbar/collection") == args.name else None
    if gate != "passed" and not args.force:
        sys.exit(f"{args.name} has no passed gate (gate: {gate}); refusing to release")
    reason = "gate passed" if gate == "passed" else f"forced, gate {gate}"
    cause = f"release {args.name} ({reason})"
    # The change-cause is copied into the new ReplicaSet, so set it before the change.
    kubectl("annotate", "deployment/api", "--overwrite", f"kubernetes.io/change-cause={cause}")
    kubectl("set", "env", "deployment/api", f"CHROMA_COLLECTION={args.name}")
    print("kubectl rollout status deployment/api")
    status = subprocess.run(
        ["kubectl", "-n", NS, "rollout", "status", "deployment/api", "--timeout=600s"]
    )
    print(kubectl("rollout", "history", "deployment/api"))
    print("to reverse: kubectl -n rahbar rollout undo deployment/api")
    return status.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Candidate, gate and rolling release.")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("candidate")
    c.add_argument("--name", required=True, help="the candidate's CHROMA_COLLECTION")
    c.add_argument("--chunk-size", type=int, required=True)
    c.add_argument("--chunk-overlap", type=int, required=True)
    c.add_argument("--skip-ingest", action="store_true", help="the collection already exists")
    p = sub.add_parser("promote")
    p.add_argument("--name", required=True)
    p.add_argument("--force", action="store_true", help="release without a passed gate")
    args = parser.parse_args()
    return candidate(args) if args.command == "candidate" else promote(args)


if __name__ == "__main__":
    sys.exit(main())
