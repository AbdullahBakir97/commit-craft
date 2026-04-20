"""Parser for conventional commit messages."""

from __future__ import annotations

import re

from src.domain.enums import CommitType

__all__ = ["ConventionalCommitParser"]


class ConventionalCommitParser:
    """Parses conventional commit messages into structured components.

    Extracts the type, scope, breaking-change indicator, description,
    and body from a commit message that follows the Conventional Commits
    specification.
    """

    PATTERN = re.compile(
        r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
        r"(?:\((?P<scope>[^)]+)\))?"
        r"(?P<breaking>!)?"
        r":\s*"
        r"(?P<description>.+)$",
        re.IGNORECASE,
    )

    def parse(self, message: str) -> dict:
        """Parse the first line of a commit message.

        Args:
            message: The full commit message (may be multi-line).

        Returns:
            A dict with keys: is_conventional, type, scope, breaking,
            description, and body.
        """
        lines = message.strip().split("\n")
        first_line = lines[0].strip()
        body = "\n".join(lines[2:]).strip() if len(lines) > 2 else None

        match = self.PATTERN.match(first_line)
        if match:
            return {
                "is_conventional": True,
                "type": CommitType(match.group("type").lower()),
                "scope": match.group("scope"),
                "breaking": bool(match.group("breaking")) or "BREAKING CHANGE" in (body or ""),
                "description": match.group("description"),
                "body": body,
            }

        return {
            "is_conventional": False,
            "type": CommitType.UNKNOWN,
            "scope": None,
            "breaking": False,
            "description": first_line,
            "body": body,
        }
