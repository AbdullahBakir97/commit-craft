"""Pydantic request and response models for the API layer."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "AnalyzeRequest",
    "AnalyzeResponse",
    "HealthResponse",
    "WebhookResponse",
]


class AnalyzeRequest(BaseModel):
    """Request body for the ``/api/v1/analyze`` endpoint."""

    message: str = Field(..., min_length=1, description="Commit message to analyse")


class AnalyzeResponse(BaseModel):
    """Response body for the ``/api/v1/analyze`` endpoint."""

    is_conventional: bool
    type: str
    score: int
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    suggested_message: str | None = None


class HealthResponse(BaseModel):
    """Response body for the ``/health`` endpoint."""

    status: str = "ok"
    uptime: float = 0.0
    version: str = "1.0.0"


class WebhookResponse(BaseModel):
    """Response body for the ``/webhook`` endpoint."""

    received: bool = True
