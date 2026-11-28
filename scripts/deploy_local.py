"""Bootstrap a real corpus without starting API ingestion or replacing live data."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from render_stack import render
from corpus_transfer import main as transfer


def apply(items: list[dict]) -> None:
    subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps({"apiVersion": "v1", "kind": "List", "items": items}), text=True, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="the source commit SHA used by make images")
    parser.add_argument("--registry", default="")
    parser.add_argument("--ollama")
    parser.add_argument("--provider-cidr", help="the single model host IPv4 address, with /32")
    args = parser.parse_args()
    if not (Path("corpus/raw/_index.json").is_file()):
        raise SystemExit("fetch and verify the real corpus first: make fetch")
    items = render(args.tag, args.registry, False, args.ollama, args.provider_cidr)
    deferred = {"Deployment", "Job", "CronJob", "HorizontalPodAutoscaler"}
    apply([o for o in items if o["kind"] not in deferred or o["metadata"]["name"] == "redis"])
    for target in ("statefulset/chroma", "deployment/redis"):
        subprocess.run(["kubectl", "-n", "rahbar", "rollout", "status", target, "--timeout=300s"], check=True)
    os.environ.update(IMAGE_TAG=args.tag, REGISTRY=args.registry)
    transfer()
    job = next(o for o in items if o["kind"] == "Job")
    job["metadata"]["name"] = f"indexer-{args.tag[:7]}-{int(time.time())}"
    apply([job])
    name = "job/" + job["metadata"]["name"]
    deadline = time.time() + 1800
    while True:
        status = json.loads(subprocess.run(["kubectl", "-n", "rahbar", "get", name, "-o", "json"],
                                           capture_output=True, text=True, check=True).stdout).get("status", {})
        if status.get("succeeded"):
            break
        if any(c.get("type") == "Failed" and c.get("status") == "True" for c in status.get("conditions", [])):
            subprocess.run(["kubectl", "-n", "rahbar", "logs", name, "--all-containers", "--tail=40"])
            raise SystemExit(f"{name} failed; see the log above and kubectl -n rahbar describe {name}")
        if time.time() > deadline:
            raise SystemExit(f"{name} did not finish within 1800 s")
        time.sleep(10)
    apply([o for o in items if o["kind"] != "Job"])
    for target in ("deployment/api", "deployment/ui"):
        subprocess.run(["kubectl", "-n", "rahbar", "rollout", "status", target, "--timeout=300s"], check=True)
    print(f"Published by {job['metadata']['name']}; API reads it without ingesting at startup.")


if __name__ == "__main__":
    main()
