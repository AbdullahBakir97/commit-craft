"""Commit Craft domain layer -- entities, enums, interfaces, and exceptions."""

from .entities import CommitAnalysis, PRAnalysisResult, SuggestedMessage
from .enums import ActionType, CheckConclusion, CommitType, QualityLevel
from .exceptions import (
    AnalysisError,
    CommitCraftError,
    ConfigurationError,
    GitHubAPIError,
)
from .interfaces import (
    AppConfig,
    ICommitAnalyzer,
    IConfigLoader,
    IGitHubClient,
    IMessageScorer,
    IMessageSuggester,
)

__all__ = [
    # Enums
    "CommitType",
    "QualityLevel",
    "CheckConclusion",
    "ActionType",
    # Entities
    "CommitAnalysis",
    "PRAnalysisResult",
    "SuggestedMessage",
    # Interfaces
    "ICommitAnalyzer",
    "IMessageScorer",
    "IMessageSuggester",
    "IGitHubClient",
    "IConfigLoader",
    "AppConfig",
    # Exceptions
    "CommitCraftError",
    "AnalysisError",
    "GitHubAPIError",
    "ConfigurationError",
]
