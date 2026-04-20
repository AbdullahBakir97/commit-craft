"""Suggests improved commit messages."""

from __future__ import annotations

import re

from src.domain.entities import SuggestedMessage
from src.domain.interfaces import IMessageSuggester

from .commit_parser import ConventionalCommitParser

__all__ = ["MessageSuggester"]

# Keyword-to-type mapping used when guessing the type of a non-conventional message.
_KEYWORD_TYPE_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bfix(e[sd])?\b", re.IGNORECASE), "fix"),
    (re.compile(r"\badd(ed|s)?\b", re.IGNORECASE), "feat"),
    (re.compile(r"\bimplement(ed|s)?\b", re.IGNORECASE), "feat"),
    (re.compile(r"\bintroduce[sd]?\b", re.IGNORECASE), "feat"),
    (re.compile(r"\bupdate[sd]?\b", re.IGNORECASE), "chore"),
    (re.compile(r"\bremove[sd]?\b", re.IGNORECASE), "chore"),
    (re.compile(r"\bdelete[sd]?\b", re.IGNORECASE), "chore"),
    (re.compile(r"\bchange[sd]?\b", re.IGNORECASE), "refactor"),
    (re.compile(r"\brefactor(ed|s)?\b", re.IGNORECASE), "refactor"),
    (re.compile(r"\btest(s|ed|ing)?\b", re.IGNORECASE), "test"),
    (re.compile(r"\bdoc(s|ument(ed|s)?)?\b", re.IGNORECASE), "docs"),
]


class MessageSuggester(IMessageSuggester):
    """Suggests improved commit messages based on conventional commit rules.

    If the original message is already well-formed, returns None.
    Otherwise, attempts to fix common issues: missing type prefix,
    capitalisation, trailing period, and excessive length.
    """

    def __init__(self) -> None:
        self._parser = ConventionalCommitParser()

    def suggest(self, message: str) -> SuggestedMessage | None:
        """Suggest an improved commit message, or None if already good.

        Args:
            message: The original commit message.

        Returns:
            A SuggestedMessage if improvements are possible, else None.
        """
        parsed = self._parser.parse(message)
        description: str = parsed["description"]
        reasons: list[str] = []
        suggested_desc = description

        # --- Fix capitalisation ---
        if suggested_desc and suggested_desc[0].isupper():
            suggested_desc = suggested_desc[0].lower() + suggested_desc[1:]
            reasons.append("lowercased first letter")

        # --- Fix trailing period ---
        if suggested_desc.endswith("."):
            suggested_desc = suggested_desc.rstrip(".")
            reasons.append("removed trailing period")

        # --- Trim to 72 chars ---
        if len(suggested_desc) > 72:
            suggested_desc = suggested_desc[:69] + "..."
            reasons.append("trimmed to 72 characters")

        # --- Build prefix ---
        if parsed["is_conventional"]:
            # Already conventional -- reconstruct with fixes applied
            prefix = parsed["type"].value
            if parsed["scope"]:
                prefix += f"({parsed['scope']})"
            if parsed["breaking"]:
                prefix += "!"
            suggested_line = f"{prefix}: {suggested_desc}"
        else:
            # Not conventional -- try to guess type
            guessed_type = self._guess_type(description)
            suggested_line = f"{guessed_type}: {suggested_desc}"
            reasons.append(f"added '{guessed_type}' type prefix")

        # Append body if present
        if parsed["body"]:
            suggested_full = f"{suggested_line}\n\n{parsed['body']}"
        else:
            suggested_full = suggested_line

        # If nothing changed, return None
        if suggested_full.strip() == message.strip():
            return None

        return SuggestedMessage(
            original=message,
            suggested=suggested_full,
            reason="; ".join(reasons) if reasons else "reformatted to conventional style",
        )

    @staticmethod
    def _guess_type(description: str) -> str:
        """Guess the commit type from keywords in the description.

        Args:
            description: The commit description text.

        Returns:
            A conventional commit type string.
        """
        for pattern, commit_type in _KEYWORD_TYPE_MAP:
            if pattern.search(description):
                return commit_type
        return "chore"
