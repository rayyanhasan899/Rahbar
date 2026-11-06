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
    subprocess.run(["kubectl", "-n", "rahbar", "wait", "--for=condition=complete", "job/" + job["metadata"]["name"], "--timeout=1800s"], check=True)
    apply([o for o in items if o["kind"] != "Job"])
    for target in ("deployment/api", "deployment/ui"):
        subprocess.run(["kubectl", "-n", "rahbar", "rollout", "status", target, "--timeout=300s"], check=True)
    print(f"Published by {job['metadata']['name']}; API reads it without ingesting at startup.")


if __name__ == "__main__":
    main()
