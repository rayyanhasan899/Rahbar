from __future__ import annotations

from pathlib import Path

ALLOWED_ROOTS = (Path(__file__).resolve().parent.parent, Path("/results"), Path("/config"))


def confined(path: Path | str) -> Path:
    resolved = Path(path).resolve()
    for root in ALLOWED_ROOTS:
        if resolved.is_relative_to(root.resolve()):
            return resolved
    raise ValueError(f"path is outside the repository, /results and /config: {path}")
