"""Every citation must name a passage that was actually retrieved (section 3.4).

eval/run_eval.py applies the same rule: source and section must match a retrieved
passage, and so must the page whenever the citation gives one.
"""

from __future__ import annotations

from ..schemas import Answer, Citation, Passage


def _matches(c: Citation, p: Passage) -> bool:
    return (
        c.source == p.source
        and str(c.section) == str(p.section)
        and (c.page is None or c.page == p.page)
    )


def check(answer: Answer, passages: list[Passage]) -> tuple[Answer, str | None]:
    """Return the answer with citations normalised, and a rejection reason or None.

    A declined answer keeps no citations. An answered one needs at least one citation,
    and every citation must match a passage. A missing page is filled in from the
    passage it matches, so the response always says where the text was.
    """
    if not answer.answered_from_context:
        return answer.model_copy(update={"citations": []}), None
    if not answer.citations:
        return answer, "an answer from context must cite at least one passage."
    fixed: list[Citation] = []
    for c in answer.citations:
        match = next((p for p in passages if _matches(c, p)), None)
        if match is None:
            return answer, (
                f'citation source "{c.source}", section "{c.section}", page {c.page} '
                "does not match any evidence passage header."
            )
        cited = Citation(source=match.source, section=match.section, page=match.page)
        if cited not in fixed:
            fixed.append(cited)
    return answer.model_copy(update={"citations": fixed}), None
