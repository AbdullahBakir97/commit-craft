"""Scores commit messages for quality on a 0-100 scale."""

from __future__ import annotations

import re

from src.domain.enums import CommitType
from src.domain.interfaces import IMessageScorer

from .commit_parser import ConventionalCommitParser

__all__ = ["MessageScorer"]

# Verbs commonly used in imperative mood commit descriptions.
_IMPERATIVE_VERBS: set[str] = {
    "add",
    "fix",
    "update",
    "remove",
    "implement",
    "refactor",
    "change",
    "create",
    "delete",
    "move",
    "rename",
    "replace",
    "improve",
    "handle",
    "set",
    "use",
    "allow",
    "make",
    "enable",
    "disable",
    "prevent",
    "ensure",
    "apply",
    "merge",
    "revert",
    "bump",
    "drop",
    "introduce",
    "extract",
    "simplify",
    "support",
    "convert",
    "migrate",
    "upgrade",
    "downgrade",
    "configure",
    "integrate",
    "expose",
    "restrict",
    "adjust",
    "clean",
    "wrap",
    "skip",
    "resolve",
}

_MERGE_RE = re.compile(r"^Merge\s", re.IGNORECASE)
_WIP_RE = re.compile(r"^(WIP|wip|fixup!|squash!)\s", re.IGNORECASE)


class MessageScorer(IMessageScorer):
    """Scores a commit message 0-100 based on conventional-commit quality rules.

    Scoring breakdown:
        - Conventional format: 25 pts
        - Description length 10-72 chars: 15 pts
        - Description starts with lowercase: 5 pts
        - Imperative mood (starts with known verb): 10 pts
        - No trailing period: 5 pts
        - Valid type present: 10 pts
        - Scope present (bonus): 5 pts
        - Body present for feat/fix (bonus): 5 pts
        - Breaking change documented: 5 pts (when applicable)
        - No WIP/fixup/squash prefix: 10 pts
        - Not a merge commit: 5 pts
    """

    def __init__(self) -> None:
        self._parser = ConventionalCommitParser()

    def score(self, message: str) -> tuple[int, list[str], list[str]]:
        """Score a commit message.

        Args:
            message: The full commit message.

        Returns:
            A tuple of (score, issues, suggestions) where score is 0-100.
        """
        issues: list[str] = []
        suggestions: list[str] = []
        total = 0

        parsed = self._parser.parse(message)
        description: str = parsed["description"]
        commit_type: CommitType = parsed["type"]
        is_conventional: bool = parsed["is_conventional"]
        body: str | None = parsed["body"]

        # --- Conventional format (25 pts) ---
        if is_conventional:
            total += 25
        else:
            issues.append("Not in conventional commit format (type: description)")
            suggestions.append("Use the format: type(scope): description  (e.g. feat(auth): add login endpoint)")

        # --- Description length 10-72 chars (15 pts) ---
        desc_len = len(description)
        if 10 <= desc_len <= 72:
            total += 15
        else:
            if desc_len < 10:
                issues.append(f"Description is too short ({desc_len} chars, minimum 10)")
                suggestions.append("Write a more descriptive commit message (at least 10 characters)")
            else:
                issues.append(f"Description exceeds 72 characters ({desc_len} chars)")
                suggestions.append("Keep the first line under 72 characters; move details to the commit body")

        # --- Description starts with lowercase (5 pts) ---
        if description and description[0].islower():
            total += 5
        else:
            issues.append("Description should start with a lowercase letter")
            suggestions.append("Start the description with a lowercase letter (e.g. 'add feature' not 'Add feature')")

        # --- Imperative mood (10 pts) ---
        first_word = description.split()[0].lower() if description.split() else ""
        if first_word in _IMPERATIVE_VERBS:
            total += 10
        else:
            issues.append("Description does not start with an imperative verb")
            suggestions.append("Start with an imperative verb like: add, fix, update, remove, implement, refactor")

        # --- No trailing period (5 pts) ---
        if not description.rstrip().endswith("."):
            total += 5
        else:
            issues.append("Description should not end with a period")
            suggestions.append("Remove the trailing period from the description")

        # --- Valid type present (10 pts) ---
        if commit_type != CommitType.UNKNOWN:
            total += 10
        else:
            issues.append("No recognized commit type")
            suggestions.append(
                "Use a standard type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
            )

        # --- Scope present — bonus (5 pts) ---
        if parsed["scope"]:
            total += 5

        # --- Body present for feat/fix — bonus (5 pts) ---
        if commit_type in (CommitType.FEAT, CommitType.FIX) and body:
            total += 5
        elif commit_type in (CommitType.FEAT, CommitType.FIX) and not body:
            suggestions.append("Consider adding a body to explain why this change was made")

        # --- Breaking change documented (5 pts) ---
        if parsed["breaking"]:
            total += 5

        # --- No WIP/fixup/squash (10 pts) ---
        first_line = message.strip().split("\n")[0]
        if not _WIP_RE.match(first_line):
            total += 10
        else:
            issues.append("Commit looks like a WIP/fixup/squash — clean up before merging")
            suggestions.append("Remove the WIP/fixup!/squash! prefix and write a proper message")

        # --- Not a merge commit (5 pts) ---
        if not _MERGE_RE.match(first_line):
            total += 5
        else:
            issues.append("Merge commits clutter PR history")
            suggestions.append("Consider rebasing instead of merging")

        # Clamp to 0-100
        total = max(0, min(100, total))

        return total, issues, suggestions
