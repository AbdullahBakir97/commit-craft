"""Abstract interfaces for Commit Craft services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .entities import CommitAnalysis, SuggestedMessage

__all__ = [
    "ICommitAnalyzer",
    "IMessageScorer",
    "IMessageSuggester",
    "IGitHubClient",
    "IConfigLoader",
    "AppConfig",
]


@dataclass(slots=True)
class AppConfig:
    """Application configuration loaded per-repository."""

    min_score: int = 70
    min_conventional_ratio: float = 0.8
    block_on_failure: bool = False
    ignored_authors: list[str] | None = None
    custom_types: list[str] | None = None


class ICommitAnalyzer(ABC):
    """Analyzes a single commit message and produces a structured result."""

    @abstractmethod
    async def analyze_commit(self, message: str, sha: str, author: str) -> CommitAnalysis:
        """Analyze a single commit message.

        Args:
            message: The full commit message.
            sha: The commit SHA.
            author: The commit author.

        Returns:
            A CommitAnalysis with score, issues, and suggestions.
        """


class IMessageScorer(ABC):
    """Scores a commit message for quality on a 0-100 scale."""

    @abstractmethod
    def score(self, message: str) -> tuple[int, list[str], list[str]]:
        """Score a commit message.

        Args:
            message: The full commit message.

        Returns:
            A tuple of (score, issues, suggestions).
        """


class IMessageSuggester(ABC):
    """Suggests improved commit messages."""

    @abstractmethod
    def suggest(self, message: str) -> SuggestedMessage | None:
        """Suggest an improved commit message, or None if already good.

        Args:
            message: The original commit message.

        Returns:
            A SuggestedMessage if improvements are possible, else None.
        """


class IGitHubClient(ABC):
    """Client for interacting with the GitHub API."""

    @abstractmethod
    async def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> None:
        """Post a comment on a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.
            body: Comment body in Markdown.
        """

    @abstractmethod
    async def create_check_run(
        self,
        owner: str,
        repo: str,
        head_sha: str,
        name: str,
        conclusion: str,
        title: str,
        summary: str,
    ) -> None:
        """Create a GitHub Check Run on a commit.

        Args:
            owner: Repository owner.
            repo: Repository name.
            head_sha: The commit SHA to attach the check to.
            name: Check run name.
            conclusion: One of success, failure, neutral.
            title: Check run output title.
            summary: Check run output summary in Markdown.
        """

    @abstractmethod
    async def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all commits for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            A list of commit dicts with sha, message, and author keys.
        """

    @abstractmethod
    async def request_changes(self, owner: str, repo: str, pr_number: int, body: str) -> None:
        """Submit a 'request changes' review on a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.
            body: Review body in Markdown.
        """


class IConfigLoader(ABC):
    """Loads per-repository configuration for Commit Craft."""

    @abstractmethod
    async def load(self, owner: str, repo: str) -> AppConfig:
        """Load configuration for a given repository.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            An AppConfig instance.
        """
