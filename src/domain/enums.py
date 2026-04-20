"""Enumerations for the Commit Craft domain layer."""

from enum import StrEnum

__all__ = ["CommitType", "QualityLevel", "CheckConclusion", "ActionType"]


class CommitType(StrEnum):
    """Conventional commit type prefixes."""

    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    BUILD = "build"
    CI = "ci"
    CHORE = "chore"
    REVERT = "revert"
    UNKNOWN = "unknown"


class QualityLevel(StrEnum):
    """Quality tier derived from a commit message score."""

    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 70-89
    FAIR = "fair"  # 50-69
    POOR = "poor"  # 30-49
    FAILING = "failing"  # 0-29


class CheckConclusion(StrEnum):
    """GitHub Check Run conclusion values."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


class ActionType(StrEnum):
    """Actions Commit Craft can take on a PR."""

    COMMENT = "comment"
    CHECK = "check"
    REQUEST_CHANGES = "request-changes"
    BLOCK = "block"
