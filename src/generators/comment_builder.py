"""Builds Markdown comments for PR analysis results."""

from __future__ import annotations

from src.domain.entities import PRAnalysisResult
from src.domain.enums import CheckConclusion

__all__ = ["CommentBuilder"]

_EMOJI_MAP = {
    CheckConclusion.SUCCESS: "white_check_mark",
    CheckConclusion.FAILURE: "x",
    CheckConclusion.NEUTRAL: "warning",
}

_SCORE_EMOJI = {
    range(90, 101): "star",
    range(70, 90): "white_check_mark",
    range(50, 70): "warning",
    range(0, 50): "x",
}


def _score_emoji(score: int) -> str:
    """Return an emoji string for a given score."""
    for r, emoji in _SCORE_EMOJI.items():
        if score in r:
            return f":{emoji}:"
    return ":grey_question:"


class CommentBuilder:
    """Builds Markdown comments summarising PR commit analysis results.

    Produces a structured comment with a summary table, per-commit
    breakdown, issues, suggestions, and a footer.
    """

    def build(self, result: PRAnalysisResult) -> str:
        """Build a Markdown comment showing commit analysis results.

        Args:
            result: The aggregated PR analysis result.

        Returns:
            A Markdown string ready to post as a GitHub comment.
        """
        sections = [
            self._header(result),
            self._summary_table(result),
            self._commit_table(result),
        ]

        if result.overall_issues:
            sections.append(self._issues_section(result))

        if result.overall_suggestions:
            sections.append(self._suggestions_section(result))

        sections.append(self._footer())
        return "\n\n".join(sections)

    @staticmethod
    def _header(result: PRAnalysisResult) -> str:
        """Build the comment header with conclusion emoji."""
        emoji = _EMOJI_MAP.get(result.conclusion, ":grey_question:")
        return f"## :{emoji}: Commit Craft Analysis"

    @staticmethod
    def _summary_table(result: PRAnalysisResult) -> str:
        """Build the summary statistics table."""
        pct = round(result.conventional_ratio * 100)
        return (
            "| Metric | Value |\n"
            "| --- | --- |\n"
            f"| Total Commits | {result.total_commits} |\n"
            f"| Conventional | {pct}% |\n"
            f"| Average Score | {result.average_score}/100 |\n"
            f"| Quality | **{result.quality_level.value.title()}** |"
        )

    @staticmethod
    def _commit_table(result: PRAnalysisResult) -> str:
        """Build the per-commit breakdown table."""
        lines = ["| SHA | Message | Score | Status |", "| --- | --- | --- | --- |"]
        for commit in result.commits:
            sha_short = commit.sha[:7]
            msg = commit.description[:50] + ("..." if len(commit.description) > 50 else "")
            emoji = _score_emoji(commit.score)
            lines.append(f"| `{sha_short}` | {msg} | {commit.score}/100 | {emoji} |")
        return "\n".join(lines)

    @staticmethod
    def _issues_section(result: PRAnalysisResult) -> str:
        """Build the issues section."""
        items = "\n".join(f"- {issue}" for issue in result.overall_issues)
        return f"### Issues\n\n{items}"

    @staticmethod
    def _suggestions_section(result: PRAnalysisResult) -> str:
        """Build the suggestions section."""
        items = "\n".join(f"- {s}" for s in result.overall_suggestions[:10])
        return f"### Suggestions\n\n{items}"

    @staticmethod
    def _footer() -> str:
        """Build the comment footer."""
        return "---\n*Powered by [Commit Craft](https://github.com/AbdullahBakir97/commit-craft)*"
