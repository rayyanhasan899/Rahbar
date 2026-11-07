"""Regression cases found in measured real model similarities."""
from dataclasses import replace
import time

from app.config import Settings
from app.services.cache import SemanticCache, intent, namespace
from tests.fakes import FakeRedis, good_answer


def test_reversed_theory_lab_outcomes_never_share_an_answer():
    cache = SemanticCache(Settings(cache_threshold=0.85), FakeRedis())
    cache.store("g", [1.0], "If I fail Theory but pass its Lab, which parts must I repeat?", good_answer())
    assert cache.lookup("g", [1.0], "If I pass Theory but fail its Lab, which parts must I repeat?") is None
    assert intent("How many courses may I repeat in summer?") != intent("How many courses may I take in summer?")


def test_old_entry_expires_even_when_another_entry_renews_hash_ttl(monkeypatch):
    cache = SemanticCache(Settings(cache_ttl=10), FakeRedis())
    now = time.time()
    monkeypatch.setattr("app.services.cache.time.time", lambda: now)
    cache.store("g", [1.0], "Attendance?", good_answer())
    monkeypatch.setattr("app.services.cache.time.time", lambda: now + 10)
    cache.store("g", [0.0], "New question?", good_answer())
    assert cache.lookup("g", [1.0], "Attendance?") is None


def test_quality_configuration_changes_invalidate_cache():
    s = Settings()
    assert namespace("g", s) != namespace("g", replace(s, relevance_floor=0.8))
    assert namespace("g", s) != namespace("g", replace(s, top_k=3))
