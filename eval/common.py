"""Shared pieces of the Assignment 3 evaluation suite (Part B, C, E).

Metrics are pure functions so the unit tests need no network. The HTTP helpers import
httpx lazily for the same reason.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
import zlib
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ALLOWED_ROOTS = (HERE.parent, Path("/results"), Path("/config"))


# files ---------------------------------------------------------------------------

def confined(path: Path | str) -> Path:
    resolved = os.path.realpath(path)
    for root in ALLOWED_ROOTS:
        base = os.path.realpath(root)
        if os.path.commonpath([base, resolved]) == base:
            return Path(resolved)
    raise ValueError(f"path is outside the repository, /results and /config: {path}")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    Path(path).write_text(text, encoding="utf-8")


def stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


# numbers -------------------------------------------------------------------------

def mean(values: Iterable[float | None]) -> float | None:
    kept = [v for v in values if v is not None]
    return sum(kept) / len(kept) if kept else None


def percentile(values: Sequence[float], q: float) -> float | None:
    """Nearest-rank percentile: the smallest value with at least q% of values at or below."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q / 100 * len(ordered)) - 1)]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


# retrieval metrics (Part B2) -----------------------------------------------------

def matches(item: dict, target: dict) -> bool:
    """A retrieved chunk hits a ground-truth entry when the source matches and either
    the page or the section matches (a chunk records the page it starts on)."""
    if item.get("source") != target.get("source"):
        return False
    page, section = target.get("page"), target.get("section")
    return (page is not None and item.get("page") == page) or (
        bool(section) and item.get("section") == section
    )


def hit_ranks(retrieved: Sequence[dict], relevant: Sequence[dict]) -> list[tuple[int, int]]:
    """(rank, target index) for the first chunk that hits each target, best rank first.
    A target counts once, so several chunks of one page cannot inflate recall."""
    seen: dict[int, int] = {}
    for rank, item in enumerate(retrieved, start=1):
        for index, target in enumerate(relevant):
            if index not in seen and matches(item, target):
                seen[index] = rank
                break
    return sorted((rank, index) for index, rank in seen.items())


def recall_at_k(retrieved: Sequence[dict], relevant: Sequence[dict], k: int) -> float | None:
    if not relevant:
        return None
    return sum(rank <= k for rank, _ in hit_ranks(retrieved, relevant)) / len(relevant)


def reciprocal_rank(retrieved: Sequence[dict], relevant: Sequence[dict]) -> float | None:
    if not relevant:
        return None
    hits = hit_ranks(retrieved, relevant)
    return 1 / hits[0][0] if hits else 0.0


def ndcg_at_k(retrieved: Sequence[dict], relevant: Sequence[dict], k: int) -> float | None:
    """Binary-gain nDCG: each target found adds 1/log2(rank+1); the ideal ranking puts
    every target first."""
    if not relevant:
        return None
    dcg = sum(1 / math.log2(rank + 1) for rank, _ in hit_ranks(retrieved, relevant) if rank <= k)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant), k) + 1))
    return dcg / ideal


def citation_validity(response: dict) -> float | None:
    """Share of citations that name a retrieved chunk (Assignment 2 definition)."""
    cites = response.get("citations") or []
    if not cites:
        return None
    retrieved = response.get("retrieved") or []

    def ok(c: dict) -> bool:
        return any(
            c.get("source") == r.get("source")
            and c.get("section") == r.get("section")
            and (c.get("page") is None or c.get("page") == r.get("page"))
            for r in retrieved
        )

    return sum(ok(c) for c in cites) / len(cites)


def with_typos(text: str, key: str, seed: int, rate: float = 0.15) -> str:
    """Swap two neighbouring letters in about `rate` of the longer words. The same key and
    seed always give the same typos, so a noise run can be repeated."""
    rng = random.Random(seed * 1_000_003 + zlib.crc32(key.encode()))
    words = text.split(" ")
    for i, word in enumerate(words):
        letters = [j for j in range(len(word) - 1) if word[j].isalpha() and word[j + 1].isalpha()]
        if len(word) > 3 and letters and rng.random() < rate:
            j = rng.choice(letters)
            words[i] = word[:j] + word[j + 1] + word[j] + word[j + 2 :]
    return " ".join(words)


# services ------------------------------------------------------------------------

class Services:
    """The API, Ollama and Chroma, as the suite talks to them."""

    def __init__(
        self,
        api: str,
        ollama: str,
        chroma: str = "",
        collection: str = "rahbar",
        host: str = "",
        timeout: float = 300.0,
    ) -> None:
        import httpx

        self.api, self.ollama, self.chroma = api.rstrip("/"), ollama.rstrip("/"), chroma.rstrip("/")
        self.collection = collection
        headers = {"Host": host} if host else {}
        self.http = httpx.Client(timeout=httpx.Timeout(timeout, connect=10), headers=headers)
        self.plain = httpx.Client(timeout=httpx.Timeout(timeout, connect=10))
        self._active: str | None = None

    def ask(self, question: str) -> tuple[dict, float, str]:
        started = time.perf_counter()
        response = self.http.post(f"{self.api}/api/ask", json={"question": question}, headers={"X-Rahbar-Cache": "bypass"})
        seconds = time.perf_counter() - started
        response.raise_for_status()
        return response.json(), seconds, response.headers.get("X-Cache", "")

    def embed(self, texts: list[str], model: str, purpose: str = "document") -> list[list[float]]:
        prefix = ""
        if model.startswith("nomic-embed-text"):
            prefix = "search_query: " if purpose == "query" else "search_document: "
        response = self.plain.post(
            f"{self.ollama}/api/embed",
            json={"model": model, "input": [prefix + t for t in texts], "truncate": False},
        )
        response.raise_for_status()
        return [[float(x) for x in v] for v in response.json()["embeddings"]]

    def chat_json(self, model: str, messages: list[dict], schema: dict, seed: int) -> dict:
        response = self.plain.post(
            f"{self.ollama}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "format": schema,
                "stream": False,
                "options": {"temperature": 0, "seed": seed, "num_ctx": 8192},
            },
        )
        response.raise_for_status()
        return json.loads(response.json()["message"]["content"])

    # Chroma's REST API, read only.
    def _root(self) -> str:
        return (
            f"{self.chroma}/api/v2/tenants/default_tenant/databases/default_database/collections"
        )

    def _collection_id(self, name: str) -> str:
        response = self.plain.get(f"{self._root()}/{name}")
        response.raise_for_status()
        return str(response.json()["id"])

    def active_collection(self) -> str:
        if self._active is None:
            control = self._collection_id(f"{self.collection}-control")
            response = self.plain.post(
                f"{self._root()}/{control}/get", json={"ids": ["active"], "include": ["metadatas"]}
            )
            response.raise_for_status()
            name = response.json()["metadatas"][0]["active_collection"]
            self._active = self._collection_id(name)
        return self._active

    def pin_collection(self, name: str) -> None:
        """Sample the same immutable generation that served evaluation queries."""
        self._active = self._collection_id(name)

    def chunk_texts(self, ids: list[str]) -> dict[str, str]:
        if not ids:
            return {}
        response = self.plain.post(
            f"{self._root()}/{self.active_collection()}/get",
            json={"ids": ids, "include": ["documents"]},
        )
        response.raise_for_status()
        data = response.json()
        return dict(zip(data["ids"], data["documents"]))

    def sample_chunks(self, n: int, seed: int) -> list[dict[str, Any]]:
        cid = self.active_collection()
        count = self.plain.get(f"{self._root()}/{cid}/count")
        count.raise_for_status()
        total = int(count.json())
        offsets = sorted(random.Random(seed).sample(range(total), min(n, total)))
        chunks = []
        for offset in offsets:
            response = self.plain.post(
                f"{self._root()}/{cid}/get",
                json={"limit": 1, "offset": offset, "include": ["documents", "metadatas"]},
            )
            response.raise_for_status()
            data = response.json()
            chunks.append(
                {"chunk_id": data["ids"][0], "text": data["documents"][0], **data["metadatas"][0]}
            )
        return chunks
