"""Deliver hash-verified public documents to the indexer's PVC, not its image."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import re
from pathlib import Path


def main() -> None:
    root = Path("corpus/raw").resolve()
    entries = json.loads((root / "_index.json").read_text())
    registry = os.environ.get("REGISTRY", "")
    image = f"{registry + '/' if registry else ''}rahbar-indexer:{os.environ.get('IMAGE_TAG', 'dev')}"
    files = []
    for entry in entries:
        name = Path(str(entry["file"])).name
        if name != entry["file"] or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:pdf|html|md|txt)", name):
            raise ValueError("corpus index must contain plain supported filenames")
        source = (root / name).resolve()
        if not source.is_relative_to(root):
            raise ValueError("corpus file escapes the selected corpus directory")
        files.append((name, source))
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"source hash mismatch: {entry['file']}")
    pod = {
        "apiVersion": "v1", "kind": "Pod", "metadata": {"name": "corpus-transfer", "namespace": "rahbar"},
        "spec": {
            "restartPolicy": "Never", "serviceAccountName": "indexer", "automountServiceAccountToken": False,
            "securityContext": {"runAsNonRoot": True, "runAsUser": 10001, "runAsGroup": 10001, "fsGroup": 10001, "seccompProfile": {"type": "RuntimeDefault"}},
            "containers": [{"name": "transfer", "image": image,
                "command": ["sleep", "1800"],
                "securityContext": {"readOnlyRootFilesystem": True, "allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]}},
                "resources": {"requests": {"cpu": "10m", "memory": "32Mi"}, "limits": {"cpu": "100m", "memory": "64Mi"}},
                "volumeMounts": [{"name": "corpus", "mountPath": "/corpus"}]}],
            "volumes": [{"name": "corpus", "persistentVolumeClaim": {"claimName": "corpus-data"}}],
        },
    }
    subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(pod), text=True, check=True)
    subprocess.run(["kubectl", "-n", "rahbar", "wait", "--for=condition=ready", "pod/corpus-transfer", "--timeout=180s"], check=True)
    with tempfile.TemporaryFile() as stream:
        with tarfile.open(fileobj=stream, mode="w") as archive:
            archive.add(root / "_index.json", arcname="_index.json")
            for name, source in files:
                archive.add(source, arcname=name)
        stream.seek(0)
        subprocess.run(["kubectl", "-n", "rahbar", "exec", "-i", "corpus-transfer", "--", "tar", "xf", "-", "-C", "/corpus"], stdin=stream, check=True)
    code = "import pathlib,json,hashlib; r=pathlib.Path('/corpus'); e=json.loads((r/'_index.json').read_text()); assert all(hashlib.sha256((r/x['file']).read_bytes()).hexdigest()==x['sha256'] for x in e); print('all PVC source hashes verified')"
    subprocess.run(["kubectl", "-n", "rahbar", "exec", "corpus-transfer", "--", "python", "-c", code], check=True)
    subprocess.run(["kubectl", "-n", "rahbar", "delete", "pod/corpus-transfer", "--wait=true"], check=True)


if __name__ == "__main__":
    main()
