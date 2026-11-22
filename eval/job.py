#!/usr/bin/env python3
"""What the evaluation Job runs (Part F2): the suite, then the release gate.

Environment: LABEL, RESULTS_DIR, GATE_FILE, plus everything suite.py reads. The
baseline is RESULTS_DIR/latest-baseline.json; the first run on a fresh volume becomes
it, and is gated against itself, so only the absolute rules (faithfulness, latency,
citation validity) can fail it. The exit code is the gate's, so
a failed gate fails the Job.
"""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    label = os.environ.get("LABEL", "run")
    results = Path(os.environ.get("RESULTS_DIR", HERE / "results"))
    gate_file = os.environ.get("GATE_FILE", str(HERE / "gate.yaml"))
    extra = os.environ.get("SUITE_ARGS", "").split()
    baseline = results / 'latest-baseline.json'
    if label == 'baseline' and (os.environ.get('CREATE_BASELINE') != 'true' or baseline.exists()):
        print('Baseline creation requires explicit CREATE_BASELINE=true and no existing baseline')
        return 2
    code = subprocess.call([sys.executable, str(HERE / "suite.py"), "--label", label, *extra])
    if code:
        print("suite failed with exit code", code)
        return code
    candidate = results / ("latest-baseline-candidate.json" if label == "baseline" else f"latest-{label}.json")
    baseline = results / "latest-baseline.json"
    if not baseline.exists() and os.environ.get("CREATE_BASELINE") != "true":
        print("Baseline missing: explicit CREATE_BASELINE=true is required")
        return 2
    if not baseline.exists():
        # The first run on a fresh volume becomes the baseline; replace it on purpose
        # only (copy another result over latest-baseline.json and say why in the report).
        shutil.copyfile(candidate, baseline)
        print("no baseline yet:", candidate.name, "saved as", baseline.name)
    decision = results / f"gate-{label}.json"
    code = subprocess.call([
        sys.executable, str(HERE / "gate.py"), "--baseline", str(baseline),
        "--candidate", str(candidate), "--thresholds", gate_file, "--out", str(decision),
    ])
    if decision.exists():
        result = json.loads(candidate.read_text())
        receipt = {'passed': code == 0, 'provenance': result.get('provenance'),
                   'config_sha256': os.environ.get('RELEASE_CONFIG_SHA256'),
                   'candidate_sha256': __import__('hashlib').sha256(candidate.read_bytes()).hexdigest(),
                   'baseline_sha256': __import__('hashlib').sha256(baseline.read_bytes()).hexdigest(),
                   'decision_sha256': __import__('hashlib').sha256(decision.read_bytes()).hexdigest()}
        receipt['provenance']['release_config_sha256'] = os.environ.get('RELEASE_CONFIG_SHA256')
        print('RAHBAR_GATE_RECEIPT=' + json.dumps(receipt), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
