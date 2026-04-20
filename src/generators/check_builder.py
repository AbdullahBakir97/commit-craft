"""Builds GitHub Check Run output from PR analysis results."""

from __future__ import annotations

from src.domain.entities import PRAnalysisResult

__all__ = ["CheckBuilder"]


class CheckBuilder:
    """Builds GitHub Check Run titles, summaries, and conclusions.

    Translates a :class:`PRAnalysisResult` into the fields required
    by the GitHub Check Runs API.
    """

    def build_title(self, result: PRAnalysisResult) -> str:
        """Build a concise check-run title.

        Args:
            result: The PR analysis result.

        Returns:
            A title like ``Commit Quality: 85/100 (Good) -- 8/10 conventional``.
        """
        quality = result.quality_level.value.title()
        return (
            f"Commit Quality: {result.average_score}/100 ({quality}) "
            f"-- {result.conventional_count}/{result.total_commits} conventional"
        )

    def build_summary(self, result: PRAnalysisResult) -> str:
        """Build a Markdown summary for the check-run output.

        Args:
            result: The PR analysis result.

        Returns:
            A Markdown string with a table and details.
        """
        pct = round(result.conventional_ratio * 100)
        lines = [
            f"**Average Score:** {result.average_score}/100",
            f"**Quality Level:** {result.quality_level.value.title()}",
            f"**Conventional Commits:** {result.conventional_count}/{result.total_commits} ({pct}%)",
            "",
            "| SHA | Message | Score |",
            "| --- | --- | --- |",
        ]

        for commit in result.commits:
            sha_short = commit.sha[:7]
            msg = commit.description[:60] + ("..." if len(commit.description) > 60 else "")
            lines.append(f"| `{sha_short}` | {msg} | {commit.score}/100 |")

        if result.overall_issues:
            lines.append("")
            lines.append("### Issues")
            for issue in result.overall_issues:
                lines.append(f"- {issue}")

        return "\n".join(lines)

    def build_conclusion(self, result: PRAnalysisResult) -> str:
        """Map the analysis conclusion to a GitHub Check conclusion string.

        Args:
            result: The PR analysis result.

        Returns:
            One of ``success``, ``failure``, or ``neutral``.
        """
        return result.conclusion.value
