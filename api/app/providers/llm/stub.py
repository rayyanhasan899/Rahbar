"""A provider with no model and no network.

Use it for every unit test and for CI (section 6): your tests must never call a
real model. It is deterministic: the same input always gives the same output.
"""

from __future__ import annotations

from collections.abc import Sequence
import re

from ...schemas import Answer, Citation, Passage, Turn


class StubProvider:
    name = "stub"

    def generate(
        self,
        question: str,
        passages: list[Passage],
        history: Sequence[Turn] = (),
        feedback: str | None = None,
    ) -> Answer:
        if not passages:
            return Answer(
                reasoning="stub: nothing was retrieved",
                answer="(stub) No passages were retrieved for this question.",
                citations=[],
                answered_from_context=False,
                confidence="low",
            )
        top = passages[0]
        tag = f"[{top.source} / {top.section}]"
        sentences = re.split(r"(?<=[.!?])\s+|\n+", top.text.strip())
        excerpt = "\n".join(f"{sentence.rstrip('.!?')} {tag}." for sentence in sentences if sentence.strip())
        return Answer(
            reasoning="stub: cites the first retrieved passage",
            answer=f"(stub) The first retrieved excerpt says: {excerpt}",
            citations=[Citation(source=top.source, section=top.section, page=top.page)],
            answered_from_context=True,
            confidence="low",
        )
