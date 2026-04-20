"""Generates a changelog from conventional commits."""

from __future__ import annotations

from collections import defaultdict
from typing import ClassVar

from src.domain.entities import CommitAnalysis

__all__ = ["ChangelogGenerator"]


class ChangelogGenerator:
    """Groups conventional commits by type and formats them as a changelog.

    Only commits that follow the conventional format are included.
    Types are ordered by importance: features first, then fixes, then
    everything else in a predefined order.
    """

    TYPE_HEADINGS: ClassVar[dict[str, str]] = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "perf": "Performance",
        "refactor": "Refactoring",
        "docs": "Documentation",
        "test": "Tests",
        "build": "Build",
        "ci": "CI/CD",
        "style": "Style",
        "chore": "Chores",
        "revert": "Reverts",
    }

    TYPE_ORDER: ClassVar[list[str]] = [
        "feat",
        "fix",
        "perf",
        "refactor",
        "docs",
        "test",
        "build",
        "ci",
        "style",
        "chore",
        "revert",
    ]

    def generate(self, commits: list[CommitAnalysis]) -> str:
        """Group conventional commits by type and format as a changelog.

        Args:
            commits: List of :class:`CommitAnalysis` results.

        Returns:
            A Markdown-formatted changelog string.
        """
        grouped: dict[str, list[CommitAnalysis]] = defaultdict(list)

        for commit in commits:
            if not commit.is_conventional:
                continue
            type_key = commit.commit_type.value
            grouped[type_key].append(commit)

        if not grouped:
            return "*No conventional commits found.*"

        sections: list[str] = []

        for type_key in self.TYPE_ORDER:
            if type_key not in grouped:
                continue
            heading = self.TYPE_HEADINGS.get(type_key, type_key.title())
            items: list[str] = []
            for commit in grouped[type_key]:
                sha_short = commit.sha[:7]
                scope_prefix = f"**{commit.scope}:** " if commit.scope else ""
                breaking_prefix = "**BREAKING:** " if commit.breaking else ""
                items.append(f"- {breaking_prefix}{scope_prefix}{commit.description} ({sha_short})")
            sections.append(f"## {heading}\n\n" + "\n".join(items))

        return "\n\n".join(sections)
