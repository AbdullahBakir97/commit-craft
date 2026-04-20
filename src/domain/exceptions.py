"""Custom exceptions for Commit Craft."""

__all__ = [
    "CommitCraftError",
    "AnalysisError",
    "GitHubAPIError",
    "ConfigurationError",
]


class CommitCraftError(Exception):
    """Base exception for all Commit Craft errors."""


class AnalysisError(CommitCraftError):
    """Raised when commit analysis fails."""


class GitHubAPIError(CommitCraftError):
    """Raised when a GitHub API call fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConfigurationError(CommitCraftError):
    """Raised when configuration is invalid or missing."""
