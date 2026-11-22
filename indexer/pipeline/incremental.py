"""Verified, content-cached ingestion with durable revisions and safe publication."""
from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path
import shutil
from typing import Any, Protocol
import uuid

from .chunk import chunk
from .clean import clean
from .config import IndexerSettings
from .datalake import Lake, atomic_json, digest, discover_inputs, identifier, load_json
from .models import Document
from .verify import check, cosine, initial_checks, version_order


class Snapshots(Protocol):
    def active(self) -> dict[str, Any] | None: ...
    def counts(self, name: str) -> dict[str, int]: ...
    def publish(self, ledger: dict, rows: Iterable[dict]) -> None: ...


Embedder = Callable[[list[str]], list[list[float]]]
Extractor = Callable[[str, str, bool], Document]


def fingerprint(settings: IndexerSettings, model_digest: str) -> str:
    return digest(json.dumps({"model": settings.embed_model, "digest": model_digest,
                              "chunk_size": settings.chunk_size,
                              "overlap": settings.chunk_overlap, "profile": 1,
                              "document_embed_chars": settings.document_embed_chars},
                             sort_keys=True).encode())


def read_ledger(lake: Lake, backend: Snapshots) -> dict | None:
    active = backend.active()
    if not active or "ledger_revision" not in active:
        return None  # First A3 run can safely replace a legacy A2 publication.
    ledger = load_json(lake.revision(active["ledger_revision"]))
    if any(ledger[k] != active[k] for k in (
            "generation", "active_collection", "fingerprint", "dimension")):
        raise ValueError("published pointer and durable ledger disagree")
    return ledger


def document_counts(ledger: dict) -> list[dict]:
    return [{"doc_id": r["doc_id"], "doc_key": key, "version": r["version"],
             "status": r["status"], "chunks": len(r["chunk_ids"]) if
             r["status"] != "deleted" else 0}
            for key, r in sorted(ledger["documents"].items())]


def snapshot_rows(lake: Lake, documents: dict) -> Iterable[dict]:
    for key, record in sorted(documents.items()):
        if record["status"] == "deleted":
            continue
        cached = load_json(lake.cache(record["cache"]))
        for row in cached["chunks"]:
            meta = {**row["metadata"], "doc_id": record["doc_id"], "doc_key": key,
                    "doc_sha256": record["sha256"], "archived": record["status"] == "archived",
                    "superseded": record["status"] == "archived"}
            yield {**row, "metadata": meta}


def classify(documents: dict, pins: dict) -> None:
    families: dict[str, list[dict]] = {}
    for record in documents.values():
        if record["status"] != "deleted":
            families.setdefault(record["doc_id"], []).append(record)
    for family, versions in families.items():
        selected = pins.get(family)
        if selected is not None and not any(r["version"] == selected for r in versions):
            raise ValueError("rollback pin does not name a verified version")
        eligible = [r["version"] for r in versions if not r.get("declared_superseded", False)]
        winner = selected or (max(eligible, key=version_order) if eligible else None)
        for record in versions:
            record["status"] = "active" if record["version"] == winner else "archived"


def materialize(lake: Lake, ledger: dict) -> None:
    """Convenience views; the pointer/revision, not these views, is authoritative."""
    for key, record in ledger["documents"].items():
        status = "current" if record["status"] == "active" else "archive"
        relative = Path(identifier(record["doc_id"])) / identifier(record["version"])
        target = lake.root / status / relative
        if status == "archive":
            target = target / record["sha256"]
        target.mkdir(parents=True, exist_ok=True)
        source = lake.blob(record["sha256"], record["source"])
        shutil.copyfile(source, target / record["source"])
        atomic_json(target / "record.json", {**record, "doc_key": key,
                                            "generation": ledger["generation"]})
        if status == "archive":
            previous_view = lake.root / "current" / relative
            # Remove only this program's materialized view; immutable objects/revisions stay.
            if (previous_view / "record.json").exists():
                for name in (record["source"], "record.json"):
                    (previous_view / name).unlink(missing_ok=True)
    atomic_json(lake.state / "ledger.json", ledger)


def ingest(settings: IndexerSettings, backend: Snapshots, embed: Embedder,
           extract: Extractor, model_digest: str, *, verify_only: bool = False,
           pins: dict | None = None) -> dict:
    lake = Lake(settings.datalake_dir, settings.collection)
    run_id = uuid.uuid4().hex
    report: dict[str, Any] = {"run_id": run_id, "collection": settings.collection,
                              "verify_only": verify_only, "documents": [],
                              "document_embeddings": 0, "chunks_embedded": 0,
                              "published": False}
    report_path = lake.root / "reports" / ("verification-" + run_id + ".json")
    try:
        return _ingest(settings, backend, embed, extract, model_digest, lake,
                       run_id, report, verify_only, pins)
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        atomic_json(report_path, report)
        print(json.dumps({"logger": "rahbar.indexer", "msg": "verification report",
                          "report": str(report_path), **report}), flush=True)


def _ingest(settings: IndexerSettings, backend: Snapshots, embed: Embedder,
            extract: Extractor, model_digest: str, lake: Lake, run_id: str,
            report: dict, verify_only: bool, pins: dict | None) -> dict:
    config = fingerprint(settings, model_digest)
    old = read_ledger(lake, backend)
    if old and old["fingerprint"] != config:
        raise ValueError("model/digest/chunk configuration changed: select a new collection")
    documents = json.loads(json.dumps(old["documents"])) if old else {}
    chosen_pins = dict(pins if pins is not None else (old or {}).get("pins", {}))
    roots = list(dict.fromkeys(Path(p).resolve() for p in (
        settings.incoming_dirs or (settings.corpus_dir,))))
    inputs = discover_inputs(roots)
    seen_locations = {(i.scope, i.source) for i in inputs}
    scopes = {str(p) for p in roots}
    verified: dict[str, dict] = {}
    rows_by_key: dict[str, dict] = {}
    analyses: dict[str, dict] = {}
    for item in inputs:
        meta = dict(item.metadata)
        version, family = str(meta["doc_version"]), str(meta["doc_id"])
        key = identifier(family + "\0" + version)
        row: dict[str, Any] = {"source": item.source, "doc_id": family, "doc_key": key,
               "version": version, "title": str(meta.get("title", "")),
               "outcome": "quarantined"}
        report["documents"].append(row)
        raw, error, doc = b"", item.error, None
        if not error:
            try:
                raw = item.path.read_bytes()
            except OSError as exc:
                error = "input read failed: " + type(exc).__name__
        sha = digest(raw)
        cache_key = digest(json.dumps({"sha": sha, "config": config,
                                      "source": item.source, "metadata": meta,
                                      "minimum": settings.min_text_chars},
                                     sort_keys=True, default=str).encode())
        cached = None
        if not error and lake.cache(cache_key).exists():
            cached = load_json(lake.cache(cache_key))
            meta.update(cached.get("resolved_metadata", {}))
            checks = cached["checks"]
        else:
            if not error:
                try:
                    doc = clean(extract(str(item.path), version, False))
                    if not meta.get("title") and doc.title:
                        meta["title"] = doc.title
                    if version == "unknown" and doc.date:
                        meta["doc_version"] = doc.date
                        doc.doc_version = doc.date
                except Exception as exc:
                    error = "extraction failed: " + type(exc).__name__
            checks = initial_checks({**meta, "source": item.source}, doc, raw, error,
                                    settings.min_text_chars)
        version = str(meta["doc_version"])
        key = identifier(family + "\0" + version)
        row.update(version=version, doc_key=key, title=str(meta.get("title", "")))
        checks = json.loads(json.dumps(checks))
        if meta.get("sha256") and meta["sha256"] != sha:
            checks["completeness"] = check(False, "manifest SHA256 differs from input bytes")
        if not family.strip() or len(family) > 200:
            checks["completeness"] = check(False, "invalid document family identity")
        if key in verified:
            checks["uniqueness"] = check(False, "conflicting duplicate document key in input scopes")
        prelim = all(checks[k]["passed"] for k in ("quality", "completeness", "recency"))
        others = {**{k: r for k, r in documents.items() if r["status"] != "deleted"},
                  **verified}
        exact = next((r for k, r in others.items() if k != key and r["sha256"] == sha), None)
        closest, nearest = -1.0, ""
        if prelim and not exact and key not in verified:
            if cached is None:
                assert doc is not None
                text = "\n".join(p.text for p in doc.pages)
                vector = embed([text[:settings.document_embed_chars]])[0]
                report["document_embeddings"] += 1
                cosine(vector, vector)  # validate finite, nonzero dimensions
                pieces = chunk(doc, settings.chunk_size, settings.chunk_overlap)
                cached = {"checks": checks, "document_vector": vector,
                          "page_count": len(doc.pages),
                          "resolved_metadata": {"title": str(meta.get("title", "")),
                                                "doc_version": version},
                          "chunks": [{"id": identifier(key + p.id), "text": p.text,
                                      "metadata": p.metadata()} for p in pieces]}
            for other_key, record in others.items():
                if other_key == key or record["doc_id"] == family:
                    continue  # Legitimate policy versions are not duplicate families.
                other = analyses.get(record["cache"]) or load_json(lake.cache(record["cache"]))
                score = cosine(cached["document_vector"], other["document_vector"])
                if score > closest:
                    closest, nearest = score, other_key
            checks["uniqueness"] = check(closest < settings.near_dup_threshold,
                "nearest other-family cosine=" + str(round(closest, 6)) + "; doc_key=" + nearest)
        elif exact:
            checks["uniqueness"] = check(False, "exact duplicate SHA256 of " + exact["source"])
        row.update(checks=checks, sha256=sha, nearest_cosine=closest,
                   page_count=(cached or {}).get("page_count", len(doc.pages) if doc else 0))
        if not all(v["passed"] for v in checks.values()):
            if cached is not None and not verify_only:
                # Near-duplicate rejection must not cause repeated document embeddings.
                cached["checks"] = checks
                atomic_json(lake.cache(cache_key), cached)
            quarantine = lake.root / "quarantine" / run_id / identifier(item.scope + item.source)
            quarantine.mkdir(parents=True, exist_ok=True)
            if raw:
                (quarantine / Path(item.source).name).write_bytes(raw)
            atomic_json(quarantine / "reason.json", row)
            continue
        assert cached is not None
        if not cached["chunks"]:
            raise ValueError("verified document has no usable chunks")
        if "vector" not in cached["chunks"][0] and not verify_only:
            vectors = embed([p["text"] for p in cached["chunks"]])
            report["chunks_embedded"] += len(vectors)
            if len(vectors) != len(cached["chunks"]):
                raise ValueError("chunk embedding count mismatch")
            for piece, vector in zip(cached["chunks"], vectors):
                cosine(vector, vector)
                if len(vector) != len(cached["document_vector"]):
                    raise ValueError("document/chunk dimension mismatch")
                piece["vector"] = vector
        cached["checks"] = checks
        analyses[cache_key] = cached
        if not verify_only:
            atomic_json(lake.cache(cache_key), cached)
            lake.blob(sha, item.source, raw)
        verified[key] = {"doc_id": family, "version": version, "source": item.source,
                         "scope": item.scope, "sha256": sha, "cache": cache_key,
                         "declared_superseded": bool(meta.get("superseded", False)),
                         "chunk_ids": [c["id"] for c in cached["chunks"]], "status": "active"}
        rows_by_key[key] = row
        previous = documents.get(key)
        row["outcome"] = "unchanged" if previous and previous["cache"] == cache_key else "accepted"
    for key, record in documents.items():
        if (record["scope"] in scopes and (record["scope"], record["source"]) not in seen_locations
                and key not in verified):
            record["status"] = "deleted"
    documents.update(verified)
    classify(documents, chosen_pins)
    for key, row in rows_by_key.items():
        record = documents[key]
        newer = [r["version"] for r in documents.values() if r["doc_id"] == record["doc_id"]
                 and r["status"] == "active" and r["version"] != record["version"]]
        row["checks"]["recency"] = check(True, "archived; active version=" + ",".join(newer)
            if record["status"] == "archived" else "selected active version (rollback pin honoured)")
        row["archived"] = record["status"] == "archived"
        if row["archived"]:
            row["outcome"] = "archived"
    report["counts"] = document_counts({"documents": documents})
    if verify_only:
        return report
    if old and documents == old["documents"] and chosen_pins == old.get("pins", {}):
        expected = {k: len(r["chunk_ids"]) for k, r in documents.items()
                    if r["status"] != "deleted" and r["chunk_ids"]}
        if backend.counts(old["active_collection"]) == expected:
            materialize(lake, old)  # Repairs a convenience-view write interrupted after publication.
            report["generation"] = old["generation"]
            return report
    active_records = [r for r in documents.values() if r["status"] != "deleted"]
    dimension = ((old or {}).get("dimension") or (len(load_json(
        lake.cache(active_records[0]["cache"]))["document_vector"]) if active_records else 0))
    if not dimension:
        report["generation"] = ""
        return report
    ledger = {"schema": 1, "documents": documents, "pins": chosen_pins,
              "fingerprint": config, "embed_model": settings.embed_model,
              "embed_model_digest": model_digest, "dimension": dimension,
              "generation": run_id, "ledger_revision": run_id,
              "active_collection": settings.collection + "-" + run_id,
              "chunk_size": settings.chunk_size, "chunk_overlap": settings.chunk_overlap,
              "chunks": sum(len(r["chunk_ids"]) for r in active_records),
              "content_sha256": digest(json.dumps(documents, sort_keys=True).encode()),
              "versions": "|".join(sorted({r["version"] for r in active_records}))}
    atomic_json(lake.revision(run_id), ledger)  # Must exist before the pointer can reference it.
    backend.publish(ledger, snapshot_rows(lake, documents))
    report.update(published=True, generation=run_id)
    materialize(lake, ledger)
    return report


def rollback(settings: IndexerSettings, backend: Snapshots, doc_id: str,
             version: str | None, model_digest: str) -> dict:
    """Restore an accepted version from the lake; never reingest or reembed inputs."""
    lake = Lake(settings.datalake_dir, settings.collection)
    old = read_ledger(lake, backend)
    if not old or old["fingerprint"] != fingerprint(settings, model_digest):
        raise ValueError("no compatible verified ledger for rollback")
    ledger = json.loads(json.dumps(old))
    if version is None:
        ledger["pins"].pop(doc_id, None)
    else:
        match = [r for r in ledger["documents"].values()
                 if r["doc_id"] == doc_id and r["version"] == version]
        if len(match) != 1:
            raise ValueError("rollback requires exactly one previously verified version")
        match[0]["status"] = "archived"
        ledger["pins"][doc_id] = version
    classify(ledger["documents"], ledger["pins"])
    if ledger["documents"] == old["documents"] and ledger["pins"] == old["pins"]:
        return {"generation": old["generation"], "published": False, "chunks_embedded": 0}
    run_id = uuid.uuid4().hex
    ledger.update(generation=run_id, ledger_revision=run_id,
                  active_collection=settings.collection + "-" + run_id)
    ledger["chunks"] = sum(len(r["chunk_ids"]) for r in ledger["documents"].values()
                           if r["status"] != "deleted")
    ledger["content_sha256"] = digest(json.dumps(ledger["documents"], sort_keys=True).encode())
    atomic_json(lake.revision(run_id), ledger)
    backend.publish(ledger, snapshot_rows(lake, ledger["documents"]))
    materialize(lake, ledger)
    result = {"generation": run_id, "published": True, "chunks_embedded": 0,
              "doc_id": doc_id, "version": version, "counts": document_counts(ledger)}
    atomic_json(lake.root / "reports" / ("rollback-" + run_id + ".json"), result)
    return result
