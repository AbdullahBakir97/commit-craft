"""Dependency injection container -- wires all layers together."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.analyzers.commit_parser import ConventionalCommitParser
from src.analyzers.message_scorer import MessageScorer
from src.analyzers.message_suggester import MessageSuggester
from src.analyzers.pr_analyzer import PRAnalyzer
from src.application.orchestrator import AnalysisOrchestrator
from src.application.webhook_handler import WebhookHandler
from src.generators.check_builder import CheckBuilder
from src.generators.comment_builder import CommentBuilder
from src.infrastructure.config.loader import ConfigLoader
from src.infrastructure.github.auth import GitHubAuthenticator
from src.infrastructure.github.client import GitHubClient
from src.infrastructure.github.webhook import WebhookVerifier

if TYPE_CHECKING:
    from src.config.settings import Settings

__all__ = ["Container"]


class Container:
    """Composes all application dependencies into a single object graph.

    Instantiated once at startup and stored on ``app.state.container``
    so that FastAPI dependency-injection helpers can retrieve individual
    components.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # --- Infrastructure ---
        self.github_auth = GitHubAuthenticator(
            settings.app_id,
            settings.get_private_key(),
        )
        self.github_client = GitHubClient(self.github_auth)
        self.webhook_verifier: WebhookVerifier | None = (
            WebhookVerifier(settings.webhook_secret) if settings.webhook_secret else None
        )
        self.config_loader = ConfigLoader(self.github_client)

        # --- Analyzers ---
        self.parser = ConventionalCommitParser()
        self.scorer = MessageScorer()
        self.suggester = MessageSuggester()
        self.pr_analyzer = PRAnalyzer(self.parser, self.scorer, self.suggester)

        # --- Generators ---
        self.comment_builder = CommentBuilder()
        self.check_builder = CheckBuilder()

        # --- Application ---
        self.orchestrator = AnalysisOrchestrator(
            self.github_client,
            self.pr_analyzer,
            self.comment_builder,
            self.check_builder,
            self.config_loader,
        )
        self.webhook_handler = WebhookHandler(self.orchestrator)
