"""Compatibility CLI; importing coverage resolves the installed coverage package."""
from __future__ import annotations
import importlib.machinery
import importlib.util
from pathlib import Path
import sys

if __name__ == "__main__":
    from query_coverage import main
    raise SystemExit(main())
else:
    here = Path(__file__).resolve().parent
    paths = [p for p in sys.path if Path(p or ".").resolve() != here]
    spec = importlib.machinery.PathFinder.find_spec("coverage", paths)
    if spec is None or spec.loader is None:
        raise ImportError("installed coverage package not found")
    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    globals().update(vars(module))
