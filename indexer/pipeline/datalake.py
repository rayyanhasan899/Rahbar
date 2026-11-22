"""Durable, atomic data-lake records and confined incoming-document discovery."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

import yaml


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".pending")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def identifier(value: str) -> str:
    """Use opaque filesystem names, never untrusted family/version strings."""
    return digest(value.encode())[:32]


@dataclass
class Incoming:
    path: Path
    scope: str
    source: str
    metadata: dict[str, Any]
    error: str = ""


def discover_inputs(roots: list[Path]) -> list[Incoming]:
    found = []
    for root in roots:
        root = root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("incoming scope is not a directory")
        manifest = root / "_index.json"
        if manifest.exists():
            entries = load_json(manifest)
            if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
                raise ValueError("incoming manifest must be a list of objects")
        else:
            entries = [{"file": p.name} for p in sorted(root.iterdir())
                       if p.suffix.lower() in {".pdf", ".md", ".txt", ".html", ".htm"}
                       and not p.name.lower().startswith(("readme", "expected"))]
        for entry in entries:
            name = str(entry.get("file", ""))
            path = root / name
            error = ""
            if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name)
                    or not path.resolve().is_relative_to(root)):
                error = "input path is not a confined plain filename"
            meta = dict(entry)
            if not error and path.suffix.lower() == ".md" and path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
                if match:
                    try:
                        front = yaml.safe_load(match[1])
                        if not isinstance(front, dict):
                            raise ValueError("front matter must be an object")
                        meta = {**front, **meta}
                    except (ValueError, yaml.YAMLError):
                        error = "invalid Markdown metadata"
                heading = re.search(r"^#\s+(.+)$", text, re.M)
                if not meta.get("title") and heading:
                    meta["title"] = heading[1].strip()
            meta.setdefault("title", meta.get("name", ""))
            meta.setdefault("source", name)
            meta.setdefault("doc_id", Path(name).stem)
            meta.setdefault("doc_version", meta.get("date", "unknown"))
            found.append(Incoming(path, str(root), name, meta, error))
    return found


class Lake:
    def __init__(self, root: str, collection: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,28}", collection):
            raise ValueError("collection prefix must be 2-29 safe characters (snapshot name limit)")
        self.root = Path(root).resolve()
        self.state = self.root / "state" / collection
        for folder in ("current", "archive", "quarantine", "reports", "objects", "cache"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    def revision(self, name: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{32}", name):
            raise ValueError("invalid ledger revision")
        return self.state / "revisions" / (name + ".json")

    def cache(self, name: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", name):
            raise ValueError("invalid cache key")
        return self.root / "cache" / (name + ".json")

    def blob(self, sha: str, source: str, data: bytes | None = None) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", sha) or Path(source).name != source:
            raise ValueError("invalid source object")
        path = self.root / "objects" / sha / source
        if data is not None and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".pending")
            temporary.write_bytes(data)
            os.replace(temporary, path)
        return path
