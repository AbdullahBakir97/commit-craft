"""Orchestrates the full PR analysis workflow."""

from __future__ import annotations

import logging
import re

from src.analyzers.pr_analyzer import PRAnalyzer
from src.domain.entities import PRAnalysisResult
from src.generators.check_builder import CheckBuilder
from src.generators.comment_builder import CommentBuilder
from src.infrastructure.config.loader import ConfigLoader
from src.infrastructure.github.client import GitHubClient

__all__ = ["AnalysisOrchestrator"]

logger = logging.getLogger(__name__)

_MERGE_RE = re.compile(r"^Merge\s", re.IGNORECASE)
_REVERT_RE = re.compile(r"^Revert\s", re.IGNORECASE)


class AnalysisOrchestrator:
    """Coordinates PR analysis: fetching commits, scoring, and reporting.

    Ties together the GitHub client, PR analyser, comment/check builders,
    and configuration loader into a single high-level workflow.
    """

    def __init__(
        self,
        github_client: GitHubClient,
        pr_analyzer: PRAnalyzer,
        comment_builder: CommentBuilder,
        check_builder: CheckBuilder,
        config_loader: ConfigLoader,
    ) -> None:
        self._client = github_client
        self._pr_analyzer = pr_analyzer
        self._comment_builder = comment_builder
        self._check_builder = check_builder
        self._config_loader = config_loader

    async def analyze_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        head_sha: str,
        installation_id: int,
    ) -> PRAnalysisResult:
        """Run the full PR analysis workflow.

        Steps:
            1. Set installation ID on the client.
            2. Load per-repo configuration.
            3. Fetch PR commits from GitHub.
            4. Filter merge/revert commits if configured.
            5. Run PR analyser.
            6. Create a GitHub Check Run.
            7. Post a comment if the action warrants it.
            8. Request changes if the action warrants it.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull-request number.
            head_sha: HEAD commit SHA.
            installation_id: GitHub App installation ID.

        Returns:
            The :class:`PRAnalysisResult` for the PR.
        """
        self._client.set_installation_id(installation_id)

        config = await self._config_loader.load(owner, repo)

        if not config.enabled:
            logger.info("Commit Craft is disabled for %s/%s", owner, repo)
            return self._empty_result(pr_number)

        commits = await self._client.get_pr_commits(owner, repo, pr_number)

        # Filter merge and revert commits if configured
        if config.ignore_merge_commits:
            commits = [c for c in commits if not _MERGE_RE.match(c.get("message", ""))]
        if config.ignore_revert_commits:
            commits = [c for c in commits if not _REVERT_RE.match(c.get("message", ""))]

        if not commits:
            logger.info("No commits to analyse for %s/%s#%d", owner, repo, pr_number)
            return self._empty_result(pr_number)

        result = await self._pr_analyzer.analyze_pr(pr_number, commits)

        # Build check run output
        title = self._check_builder.build_title(result)
        summary = self._check_builder.build_summary(result)
        conclusion = self._check_builder.build_conclusion(result)

        # Always create the check run
        await self._client.create_check_run(
            owner=owner,
            repo=repo,
            head_sha=head_sha,
            name="Commit Craft",
            title=title,
            summary=summary,
            conclusion=conclusion,
        )

        # Post comment if action requires it
        if config.action in ("comment", "request-changes", "block"):
            comment = self._comment_builder.build(result)
            await self._client.post_comment(owner, repo, pr_number, comment)

        # Request changes if action requires it and the check failed
        if config.action in ("request-changes", "block") and not result.passed:
            comment = self._comment_builder.build(result)
            await self._client.request_changes(owner, repo, pr_number, comment)

        logger.info(
            "Analysis complete for %s/%s#%d: score=%d conclusion=%s",
            owner,
            repo,
            pr_number,
            result.average_score,
            conclusion,
        )

        return result

    @staticmethod
    def _empty_result(pr_number: int) -> PRAnalysisResult:
        """Create an empty result for skipped PRs.

        Args:
            pr_number: The pull-request number.

        Returns:
            A minimal :class:`PRAnalysisResult`.
        """
        from src.domain.enums import CheckConclusion, QualityLevel

        return PRAnalysisResult(
            pr_number=pr_number,
            total_commits=0,
            conventional_count=0,
            non_conventional_count=0,
            average_score=0,
            quality_level=QualityLevel.FAILING,
            commits=[],
            overall_issues=[],
            overall_suggestions=[],
            conclusion=CheckConclusion.NEUTRAL,
        )
