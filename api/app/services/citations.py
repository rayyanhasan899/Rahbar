"""Every citation must name a passage that was actually retrieved (section 3.4).

eval/run_eval.py applies the same rule: source and section must match a retrieved
passage, and so must the page whenever the citation gives one.
"""

from __future__ import annotations
import re

from ..schemas import Answer, Citation, Passage


def _matches(c: Citation, p: Passage) -> bool:
    return (
        c.source == p.source
        and str(c.section) == str(p.section)
        and (c.page is None or c.page == p.page)
    )


def inline_problem(text: str, citations: list[Citation]) -> str | None:
    """Check sentence-level attribution syntax, not semantic entailment.

    Hide exact validated tags before splitting, so filename dots and clause
    decimals are not sentence boundaries. Citations after punctuation are also
    accepted. Each sentence/line must finish with at least one validated tag.
    """
    marker = "§CITE§"
    if marker in text or not text.strip():
        return "answer must contain cited factual sentences."
    allowed = {f"{c.source} / {c.section}" for c in citations}
    if any(tag not in allowed for tag in re.findall(r"\[([^\]\n]+ / [^\]\n]+)\]", text)):
        return "inline citation does not match the validated citation list."
    masked = text
    for c in citations:
        masked = masked.replace(f"[{c.source} / {c.section}]", marker)
    masked = re.sub(r"([.!?])\s*(" + re.escape(marker) + r")", r" \2\1", masked)
    sentences = re.split(r"(?<=[.!?])\s+|\n+", masked.strip())
    if any(not re.search(re.escape(marker) + r"(?:\s*" + re.escape(marker) + r")*[.!?]?\s*$", s) for s in sentences if s.strip()):
        return "every factual sentence must end with an exact [source / section] citation."
    return None


def check(answer: Answer, passages: list[Passage]) -> tuple[Answer, str | None]:
    """Return the answer with citations normalised, and a rejection reason or None.

    A declined answer keeps no citations. An answered one needs at least one citation,
    and every citation must match a passage. A missing page is filled in from the
    passage it matches, so the response always says where the text was.
    """
    if not answer.answered_from_context:
        if answer.confidence != "low":
            return answer, (
                "a refusal must have low confidence. If evidence supports your factual "
                "answer, set answered_from_context to true and supply exact citations."
            )
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
    problem = inline_problem(answer.answer, fixed)
    return answer.model_copy(update={"citations": fixed}), problem
