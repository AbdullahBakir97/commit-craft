"""Webhook event handler for Commit Craft."""

from __future__ import annotations

import logging
from typing import Any

from .orchestrator import AnalysisOrchestrator

__all__ = ["WebhookHandler"]

logger = logging.getLogger(__name__)

_PR_ACTIONS = {"opened", "synchronize", "reopened"}


class WebhookHandler:
    """Routes incoming GitHub webhook events to the appropriate handler.

    Currently handles ``pull_request`` events for opened, synchronize,
    and reopened actions.
    """

    def __init__(self, orchestrator: AnalysisOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def handle_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Dispatch a webhook event to the correct handler.

        Args:
            event_type: The GitHub event type (``X-GitHub-Event`` header).
            payload: The parsed JSON payload.
        """
        match event_type:
            case "pull_request":
                action = payload.get("action", "")
                if action in _PR_ACTIONS:
                    await self._handle_pr(payload)
                else:
                    logger.debug("Ignoring pull_request action: %s", action)
            case _:
                logger.debug("Ignoring event type: %s", event_type)

    async def _handle_pr(self, payload: dict[str, Any]) -> None:
        """Handle a pull_request event by running the analysis orchestrator.

        Args:
            payload: The pull_request webhook payload.
        """
        pr = payload["pull_request"]
        owner = payload["repository"]["owner"]["login"]
        repo = payload["repository"]["name"]
        pr_number = pr["number"]
        head_sha = pr["head"]["sha"]
        installation_id = payload["installation"]["id"]

        logger.info("Handling PR %s/%s#%d (sha=%s)", owner, repo, pr_number, head_sha[:8])

        await self._orchestrator.analyze_pr(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            installation_id=installation_id,
        )
