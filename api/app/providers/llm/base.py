"""The LLM provider interface (section 3.5). Swapping providers is one file."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ...schemas import Answer, Passage, Turn


class LLMProvider(Protocol):
    name: str

    def generate(
        self,
        question: str,
        passages: list[Passage],
        history: Sequence[Turn] = (),
        feedback: str | None = None,
    ) -> Answer:
        """Answer the question from the passages, as an `Answer`.

        `feedback` is set on the single retry and says why the first reply was rejected.
        Raise ProviderOutputError for an unparseable reply and ProviderUnavailable when
        the model cannot be reached (both in prompt.py).
        """
        ...
