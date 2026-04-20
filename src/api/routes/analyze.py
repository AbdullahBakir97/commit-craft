"""Public analysis endpoint for the dashboard demo."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from src.api.dependencies import get_container
from src.api.schemas import AnalyzeRequest, AnalyzeResponse
from src.container import Container

__all__ = ["router"]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(
    request: AnalyzeRequest,
    container: Container = Depends(get_container),
) -> AnalyzeResponse:
    """Run commit message analysis on arbitrary text.

    This endpoint is intended for the interactive dashboard demo and
    does not require GitHub authentication.

    Args:
        request: The analysis request containing a commit message.
        container: The DI container (injected).

    Returns:
        An :class:`AnalyzeResponse` with conventional-commit parsing,
        score, issues, suggestions, and a suggested message.
    """
    message = request.message

    parsed = container.parser.parse(message)
    score, issues, suggestions = container.scorer.score(message)
    suggested = container.suggester.suggest(message)

    return AnalyzeResponse(
        is_conventional=parsed["is_conventional"],
        type=parsed["type"].value,
        score=score,
        issues=issues,
        suggestions=suggestions,
        suggested_message=suggested.suggested if suggested else None,
    )
