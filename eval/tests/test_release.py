"""Release configuration consistency using an isolated in-memory kubectl recorder."""

import copy
import importlib.util
import json
from pathlib import Path
from argparse import Namespace
import pytest

spec = importlib.util.spec_from_file_location(
    "release", Path(__file__).resolve().parents[2] / "scripts/release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def cluster(monkeypatch):
    old = {"CHROMA_COLLECTION": "old", "CHUNK_SIZE": "400", "CHUNK_OVERLAP": "50"}
    new = {**old, "CHROMA_COLLECTION": "cand", "CHUNK_SIZE": "700"}
    config = release.immutable_config(new)
    cfgname = config["metadata"]["name"]

    def pod(name):
        return {
            "metadata": {},
            "spec": {
                "containers": [
                    {"image": "api:sha", "envFrom": [{"configMapRef": {"name": name}}]}
                ]
            },
        }

    candidate = {"metadata": {"annotations": {}}, "spec": {"template": pod(cfgname)}}
    index = {
        "name": "cand",
        "active_collection": "cand-g",
        "generation": "g",
        "fingerprint": "f",
        "corpus_sha256": "c",
        "embed_model_digest": "d",
    }
    receipt = {
        "passed": True,
        "provenance": {
            "index": index,
            "corpus_sha256": "c",
            "embedding_digest": "d",
            "release_config_sha256": release.digest(new),
        },
        **{
            key: "a" * 64
            for key in ("candidate_sha256", "baseline_sha256", "decision_sha256")
        },
    }
    binding = {
        "receipt": receipt,
        "config": cfgname,
        "config_sha256": release.digest(new),
        "template_sha256": release.digest(candidate["spec"]["template"]),
        "job_name": "eval-cand",
        "job_uid": "uid",
        "indexer_image": "indexer:new",
    }
    candidate["metadata"]["annotations"] = {
        "rahbar/gate": "passed",
        "rahbar/collection": "cand",
        "rahbar/receipt": json.dumps(binding),
    }
    data = {
        ("deployment", "api-candidate"): candidate,
        ("deployment", "api"): {
            "metadata": {},
            "spec": {"template": pod("rahbar-config")},
        },
        ("configmap", "rahbar-config"): {
            "metadata": {"name": "rahbar-config"},
            "data": old,
        },
        ("configmap", cfgname): config,
        ("job", "eval-cand"): {"metadata": {"uid": "uid"}, "status": {"succeeded": 1}},
        ("jobs", ""): {"items": []},
        ("cronjob", "reindex"): {
            "metadata": {},
            "spec": {
                "suspend": False,
                "jobTemplate": {"spec": {"template": pod("rahbar-config")}},
            },
        },
    }
    data[("cronjob", "reindex")]["spec"]["jobTemplate"]["spec"]["template"]["spec"][
        "containers"
    ][0]["image"] = "indexer:old"
    mutations, history = [], []

    def get(kind, name):
        return copy.deepcopy(data[(kind, name)])

    def merge(target, incoming):
        for key, value in incoming.items():
            if isinstance(value, dict):
                merge(target.setdefault(key, {}), value)
            else:
                target[key] = copy.deepcopy(value)

    def patch(kind, name, value):
        mutations.append((kind, name, value))
        if kind == "deployment":
            history.append(copy.deepcopy(data[(kind, name)]["spec"]["template"]))
        merge(data[(kind, name)], value)

    def apply(obj):
        data[("configmap", obj["metadata"]["name"])] = copy.deepcopy(obj)

    def kubectl(*args, **kwargs):
        if args[:2] == ("rollout", "undo"):
            data[("deployment", "api")]["spec"]["template"] = history[-1]
        return ""

    monkeypatch.setattr(release, "get", get)
    monkeypatch.setattr(release, "patch", patch)
    monkeypatch.setattr(release, "apply", apply)
    monkeypatch.setattr(release, "kubectl", kubectl)
    monkeypatch.setattr(release, "rollout", lambda: None)
    monkeypatch.setattr(release, "index_state", lambda deployment: index)
    return data, mutations


def test_failed_or_stale_gate_does_not_mutate_live(monkeypatch):
    data, mutations = cluster(monkeypatch)
    data[("deployment", "api-candidate")]["metadata"]["annotations"]["rahbar/gate"] = (
        "failed"
    )
    with pytest.raises(ValueError, match="no passed"):
        release.promote(Namespace(name="cand"))
    assert not mutations


def test_changed_template_cannot_reuse_gate_receipt(monkeypatch):
    data, mutations = cluster(monkeypatch)
    data[("deployment", "api-candidate")]["spec"]["template"]["spec"]["containers"][0][
        "image"
    ] = "different:sha"
    with pytest.raises(ValueError, match="template changed"):
        release.promote(Namespace(name="cand"))
    assert not mutations


def test_promote_and_undo_keep_reader_and_writer_config_and_image_consistent(
    monkeypatch,
):
    data, mutations = cluster(monkeypatch)
    assert release.promote(Namespace(name="cand")) == 0

    def selected(kind):
        spec = (
            data[("deployment", "api")]["spec"]["template"]["spec"]
            if kind == "api"
            else data[("cronjob", "reindex")]["spec"]["jobTemplate"]["spec"][
                "template"
            ]["spec"]
        )
        c = spec["containers"][0]
        return c["envFrom"][0]["configMapRef"]["name"], c["image"]

    assert selected("api")[0] == selected("cron")[0]
    assert selected("cron")[1] == "indexer:new"
    assert not data[("cronjob", "reindex")]["spec"]["suspend"]
    release.undo()
    assert selected("api")[0] == selected("cron")[0]
    assert selected("cron")[1] == "indexer:old"
    assert data[("configmap", selected("api")[0])]["data"]["CHROMA_COLLECTION"] == "old"
