from __future__ import annotations

import os
from pathlib import Path

ALLOWED_ROOTS = (Path(__file__).resolve().parent.parent, Path("/results"), Path("/config"))


def confined(path: Path | str) -> Path:
    resolved = os.path.realpath(path)
    for root in ALLOWED_ROOTS:
        base = os.path.realpath(root)
        if os.path.commonpath([base, resolved]) == base:
            return Path(resolved)
    raise ValueError(f"path is outside the repository, /results and /config: {path}")
