"""Load per-repository configuration from .github/commit-craft.yml."""

from __future__ import annotations

import logging

import yaml
from pydantic import ValidationError

from src.infrastructure.github.client import GitHubClient

from .schema import CommitCraftConfig

__all__ = ["ConfigLoader"]

logger = logging.getLogger(__name__)

_CONFIG_PATH = ".github/commit-craft.yml"


class ConfigLoader:
    """Loads and validates per-repo Commit Craft configuration via the GitHub API.

    Falls back to sensible defaults when the file is missing or contains
    invalid YAML.
    """

    def __init__(self, github_client: GitHubClient) -> None:
        self._client = github_client

    async def load(self, owner: str, repo: str) -> CommitCraftConfig:
        """Load configuration for *owner/repo*.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            A validated :class:`CommitCraftConfig` instance.
        """
        content = await self._client.get_file_content(owner, repo, _CONFIG_PATH)

        if content is None:
            logger.debug("No config file found for %s/%s -- using defaults", owner, repo)
            return CommitCraftConfig()

        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                logger.warning("Config for %s/%s is not a mapping -- using defaults", owner, repo)
                return CommitCraftConfig()
            return CommitCraftConfig(**data)
        except yaml.YAMLError as exc:
            logger.warning("Invalid YAML in config for %s/%s: %s -- using defaults", owner, repo, exc)
            return CommitCraftConfig()
        except ValidationError as exc:
            logger.warning("Invalid config for %s/%s: %s -- using defaults", owner, repo, exc)
            return CommitCraftConfig()
