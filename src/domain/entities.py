"""Domain entities for Commit Craft."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import CheckConclusion, CommitType, QualityLevel

__all__ = ["CommitAnalysis", "PRAnalysisResult", "SuggestedMessage"]


@dataclass(slots=True)
class CommitAnalysis:
    """Analysis result for a single commit message."""

    sha: str
    message: str
    author: str
    is_conventional: bool
    commit_type: CommitType
    scope: str | None
    description: str
    body: str | None
    breaking: bool
    score: int  # 0-100
    issues: list[str]  # list of problems found
    suggestions: list[str]  # list of improvement suggestions


@dataclass(slots=True)
class PRAnalysisResult:
    """Aggregated analysis result for all commits in a PR."""

    pr_number: int
    total_commits: int
    conventional_count: int
    non_conventional_count: int
    average_score: int
    quality_level: QualityLevel
    commits: list[CommitAnalysis]
    overall_issues: list[str]
    overall_suggestions: list[str]
    conclusion: CheckConclusion

    @property
    def conventional_ratio(self) -> float:
        """Ratio of conventional commits to total commits."""
        return self.conventional_count / max(self.total_commits, 1)

    @property
    def passed(self) -> bool:
        """Whether the PR passed the quality check."""
        return self.conclusion == CheckConclusion.SUCCESS


@dataclass(slots=True)
class SuggestedMessage:
    """A suggested improved commit message."""

    original: str
    suggested: str
    reason: str
