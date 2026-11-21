"""scripts/release.py without a cluster: kubectl is replaced by a recorder."""

import sys
from argparse import Namespace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import release  # noqa: E402


def test_use_config_swaps_only_the_live_configmap():
    pod = {"containers": [{"envFrom": [{"configMapRef": {"name": "rahbar-config"}},
                                       {"secretRef": {"name": "rahbar-secret"}}]}],
           "initContainers": [{"envFrom": [{"configMapRef": {"name": "rahbar-config"}}]}]}
    release.use_config(pod, "rahbar-config-candidate")
    assert pod["containers"][0]["envFrom"][0]["configMapRef"]["name"] == "rahbar-config-candidate"
    assert pod["containers"][0]["envFrom"][1] == {"secretRef": {"name": "rahbar-secret"}}
    assert pod["initContainers"][0]["envFrom"][0]["configMapRef"]["name"].endswith("candidate")


def fake_cluster(monkeypatch, annotations):
    calls = []

    def kubectl(*args, stdin=None, check=True):
        calls.append(args)
        return ""

    monkeypatch.setattr(release, "kubectl", kubectl)
    deployment = {"metadata": {"annotations": annotations}}
    monkeypatch.setattr(release, "get", lambda kind, name: deployment)
    monkeypatch.setattr(release.subprocess, "run", lambda *a, **k: Namespace(returncode=0))
    return calls


def test_promote_refuses_a_candidate_whose_gate_failed(monkeypatch):
    calls = fake_cluster(monkeypatch, {"rahbar/gate": "failed", "rahbar/collection": "cand"})
    with pytest.raises(SystemExit, match="no passed gate"):
        release.promote(Namespace(name="cand", force=False))
    assert not any("set" in c for c in calls)


def test_promote_ignores_a_gate_recorded_for_another_collection(monkeypatch):
    fake_cluster(monkeypatch, {"rahbar/gate": "passed", "rahbar/collection": "older"})
    with pytest.raises(SystemExit):
        release.promote(Namespace(name="cand", force=False))


def test_promote_annotates_before_changing_the_collection(monkeypatch):
    calls = fake_cluster(monkeypatch, {"rahbar/gate": "passed", "rahbar/collection": "cand"})
    assert release.promote(Namespace(name="cand", force=False)) == 0
    annotate = next(i for i, c in enumerate(calls) if c[0] == "annotate")
    set_env = next(i for i, c in enumerate(calls) if c[0] == "set")
    assert annotate < set_env
    assert "CHROMA_COLLECTION=cand" in calls[set_env]
    assert "kubernetes.io/change-cause=release cand (gate passed)" in calls[annotate]


def test_forced_promote_records_why(monkeypatch):
    calls = fake_cluster(monkeypatch, {"rahbar/gate": "failed", "rahbar/collection": "bad"})
    release.promote(Namespace(name="bad", force=True))
    assert any("forced, gate failed" in " ".join(c) for c in calls)
