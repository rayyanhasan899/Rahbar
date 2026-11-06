"""Render the same base for a real laptop corpus or owned CI fixtures.

Output is JSON Kubernetes List so substitutions never depend on shell escaping.
No credentials are read. The indexer image contains code only, never source PDFs.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
import yaml


def render(tag: str, registry: str, fixture: bool, ollama: str | None, cidr: str | None) -> list[dict]:
    raw = subprocess.check_output(["kubectl", "kustomize", "k8s/overlays/prod"], text=True)
    items = list(yaml.safe_load_all(raw))
    for obj in items:
        kind = obj["kind"]
        if kind == "ConfigMap":
            if ollama:
                obj["data"]["OLLAMA_URL"] = ollama
            if fixture:
                obj["data"].update(LLM_PROVIDER="stub", RELEVANCE_FLOOR="0.65", CHUNK_SIZE="400", CHUNK_OVERLAP="50")
        if kind == "NetworkPolicy" and cidr:
            for rule in obj["spec"].get("egress", []):
                for target in rule.get("to", []):
                    if target.get("ipBlock", {}).get("cidr") == "192.168.65.254/32":
                        target["ipBlock"]["cidr"] = cidr
        if kind in {"Deployment", "StatefulSet", "Job", "CronJob"}:
            spec = obj["spec"]
            if kind == "CronJob":
                spec["suspend"] = fixture
                spec = spec["jobTemplate"]["spec"]
            pod = spec["template"]["spec"]
            for container in pod.get("containers", []) + pod.get("initContainers", []):
                for component in ("api", "ui", "indexer"):
                    if container["image"].startswith(f"rahbar-{component}:"):
                        container["image"] = f"{registry + '/' if registry else ''}rahbar-{component}:{tag}"
            if fixture:
                for volume in pod.get("volumes", []):
                    if volume["name"] == "corpus":
                        volume.pop("persistentVolumeClaim", None)
                        volume["configMap"] = {"name": "fixture-corpus"}
    return items


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tag", default="dev")
    p.add_argument("--registry", default="")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--ollama")
    p.add_argument("--provider-cidr")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    items = render(args.tag, args.registry, args.fixture, args.ollama, args.provider_cidr)
    args.out.write_text(json.dumps({"apiVersion": "v1", "kind": "List", "items": items}, indent=2))


if __name__ == "__main__":
    main()
