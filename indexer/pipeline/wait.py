"""Bounded dependency bootstrap, before the indexer's retry budget starts."""

import os
import time
from urllib.request import urlopen
from urllib.error import URLError


def main() -> None:
    host = os.environ.get("CHROMA_HOST", "chroma")
    port = os.environ.get("CHROMA_PORT", "8000")
    for _ in range(120):
        try:
            with urlopen(f"http://{host}:{port}/api/v2/heartbeat", timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            pass
        time.sleep(2)
    raise SystemExit("Chroma heartbeat unavailable after bounded bootstrap wait")


if __name__ == "__main__":
    main()
