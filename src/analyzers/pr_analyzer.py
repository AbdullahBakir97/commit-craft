"""Orchestrates analysis of all commits in a pull request."""

from __future__ import annotations

from src.domain.entities import CommitAnalysis, PRAnalysisResult
from src.domain.enums import CheckConclusion, QualityLevel

from .commit_parser import ConventionalCommitParser
from .message_scorer import MessageScorer
from .message_suggester import MessageSuggester

__all__ = ["PRAnalyzer"]


class PRAnalyzer:
    """Analyzes every commit in a PR and produces an aggregated quality report.

    Uses a ConventionalCommitParser, MessageScorer, and MessageSuggester
    internally to evaluate each commit and derive an overall conclusion.
    """

    def __init__(
        self,
        parser: ConventionalCommitParser,
        scorer: MessageScorer,
        suggester: MessageSuggester,
    ) -> None:
        self._parser = parser
        self._scorer = scorer
        self._suggester = suggester

    async def analyze_pr(self, pr_number: int, commits: list[dict]) -> PRAnalysisResult:
        """Analyze all commits in a PR and produce an aggregated result.

        Args:
            pr_number: The pull request number.
            commits: A list of commit dicts, each containing 'sha',
                     'message', and 'author' keys.

        Returns:
            A PRAnalysisResult with per-commit analyses and overall metrics.
        """
        analyses: list[CommitAnalysis] = []
        for commit in commits:
            analysis = self._analyze_single(commit)
            analyses.append(analysis)

        total = len(analyses)
        conventional_count = sum(1 for a in analyses if a.is_conventional)
        non_conventional_count = total - conventional_count
        avg_score = sum(a.score for a in analyses) // max(total, 1)
        ratio = conventional_count / max(total, 1)

        # Determine conclusion
        if avg_score >= 70 and ratio >= 0.8:
            conclusion = CheckConclusion.SUCCESS
        elif avg_score >= 50:
            conclusion = CheckConclusion.NEUTRAL
        else:
            conclusion = CheckConclusion.FAILURE

        quality_level = self._get_quality_level(avg_score)

        # Collect overall issues and suggestions (deduplicated)
        overall_issues: list[str] = []
        overall_suggestions: list[str] = []
        seen_issues: set[str] = set()
        seen_suggestions: set[str] = set()

        for analysis in analyses:
            for issue in analysis.issues:
                if issue not in seen_issues:
                    seen_issues.add(issue)
                    overall_issues.append(issue)
            for suggestion in analysis.suggestions:
                if suggestion not in seen_suggestions:
                    seen_suggestions.add(suggestion)
                    overall_suggestions.append(suggestion)

        return PRAnalysisResult(
            pr_number=pr_number,
            total_commits=total,
            conventional_count=conventional_count,
            non_conventional_count=non_conventional_count,
            average_score=avg_score,
            quality_level=quality_level,
            commits=analyses,
            overall_issues=overall_issues,
            overall_suggestions=overall_suggestions,
            conclusion=conclusion,
        )

    def _analyze_single(self, commit: dict) -> CommitAnalysis:
        """Analyze a single commit.

        Args:
            commit: A dict with 'sha', 'message', and 'author' keys.

        Returns:
            A CommitAnalysis for the commit.
        """
        sha: str = commit["sha"]
        message: str = commit["message"]
        author: str = commit["author"]

        parsed = self._parser.parse(message)
        score, issues, suggestions = self._scorer.score(message)

        # Add a suggestion from the suggester if available
        suggested = self._suggester.suggest(message)
        if suggested:
            suggestions.append(f"Suggested: {suggested.suggested}")

        return CommitAnalysis(
            sha=sha,
            message=message,
            author=author,
            is_conventional=parsed["is_conventional"],
            commit_type=parsed["type"],
            scope=parsed["scope"],
            description=parsed["description"],
            body=parsed["body"],
            breaking=parsed["breaking"],
            score=score,
            issues=issues,
            suggestions=suggestions,
        )

    @staticmethod
    def _get_quality_level(score: int) -> QualityLevel:
        """Map a numeric score to a QualityLevel.

        Args:
            score: The average score (0-100).

        Returns:
            The corresponding QualityLevel.
        """
        if score >= 90:
            return QualityLevel.EXCELLENT
        if score >= 70:
            return QualityLevel.GOOD
        if score >= 50:
            return QualityLevel.FAIR
        if score >= 30:
            return QualityLevel.POOR
        return QualityLevel.FAILING
