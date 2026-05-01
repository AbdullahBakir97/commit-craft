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

# WIP/fixup/squash prefixes that should be stripped before suggesting.
_WIP_PREFIX_RE = re.compile(
    r"^(?:wip[!:\s\-]*|fixup[!:\s\-]*|squash[!:\s\-]*|tmp[:\s]*|draft[:\s]*)",
    re.IGNORECASE,
)

# Past-tense verbs at the start of a description that should be converted to
# imperative form. Maps the past-tense form to its imperative replacement.
_PAST_TO_IMPERATIVE: dict[str, str] = {
    "fixed": "fix",
    "fixes": "fix",
    "added": "add",
    "adds": "add",
    "removed": "remove",
    "removes": "remove",
    "deleted": "delete",
    "deletes": "delete",
    "updated": "update",
    "updates": "update",
    "changed": "change",
    "changes": "change",
    "refactored": "refactor",
    "refactors": "refactor",
    "improved": "improve",
    "improves": "improve",
    "implemented": "implement",
    "implements": "implement",
    "introduced": "introduce",
    "introduces": "introduce",
    "renamed": "rename",
    "renames": "rename",
    "replaced": "replace",
    "replaces": "replace",
    "moved": "move",
    "moves": "move",
    "tested": "test",
    "tests": "test",
    "documented": "document",
    "documents": "document",
}


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

        # --- Strip WIP/fixup/squash prefixes ---
        # These should never reach `main` — strip them before any other cleanup
        # so the resulting suggestion captures the real intent of the commit.
        wip_match = _WIP_PREFIX_RE.match(suggested_desc)
        if wip_match:
            suggested_desc = suggested_desc[wip_match.end() :].lstrip()
            reasons.append("stripped WIP/fixup prefix")

        # --- Convert past-tense verbs to imperative ---
        # `Fixed login bug` → `fix login bug`. We match only the first token so
        # we don't accidentally rewrite past-tense words inside the description.
        first_word_match = re.match(r"^(\w+)(\s+.*)$", suggested_desc, re.DOTALL)
        if first_word_match:
            first_word = first_word_match.group(1).lower()
            rest = first_word_match.group(2)
            if first_word in _PAST_TO_IMPERATIVE:
                suggested_desc = _PAST_TO_IMPERATIVE[first_word] + rest
                reasons.append(f"converted '{first_word_match.group(1)}' to imperative")

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
            # Not conventional -- try to guess type.
            guessed_type = self._guess_type(description)

            # Avoid producing `fix: fix login bug` when the first word of the
            # description has already been normalised to the type's verb form.
            # We strip the leading verb if it matches the guessed type.
            first_token = suggested_desc.split(maxsplit=1)
            if first_token and first_token[0].lower() == guessed_type:
                suggested_desc = first_token[1] if len(first_token) > 1 else ""

            suggested_line = f"{guessed_type}: {suggested_desc}".strip()
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
