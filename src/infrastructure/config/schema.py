"""Pydantic models for per-repository configuration (.github/commit-craft.yml)."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["CommitCraftConfig"]

_DEFAULT_TYPES: list[str] = [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
]


class CommitCraftConfig(BaseModel):
    """Per-repository configuration for Commit Craft.

    Loaded from ``.github/commit-craft.yml`` in the target repository.
    All fields have sensible defaults so the config file is optional.
    """

    enabled: bool = True
    require_conventional: bool = True
    min_score: int = Field(default=60, ge=0, le=100)
    action: str = Field(default="check", description="check | comment | request-changes | block")
    allowed_types: list[str] = Field(default_factory=lambda: list(_DEFAULT_TYPES))
    max_subject_length: int = 72
    require_scope: bool = False
    require_body: bool = False
    ignore_merge_commits: bool = True
    ignore_revert_commits: bool = True
