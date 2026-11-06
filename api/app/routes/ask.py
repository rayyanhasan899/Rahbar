"""POST /api/ask. The Ingress sends /api/* here unchanged, so the prefix stays."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response

from ..schemas import AskRequest, AskResponse
from ..services.answer import RetrievalUnavailable, answer_question

router = APIRouter(prefix="/api")


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request, response: Response) -> AskResponse:
    state = request.app.state
    try:
        result = answer_question(
            body.question,
            state.retriever,
            state.provider,
            state.settings,
            history=body.history,
            cache=getattr(state, "cache", None),
        )
    except RetrievalUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if result.cache != "bypass":
        response.headers["X-Cache"] = result.cache.upper()
    return result.response
