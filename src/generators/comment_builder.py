"""Builds Markdown comments for PR commit analysis results.

The output reads like a senior maintainer wrote it: each non-passing commit
gets a focused "what's wrong + suggested rewrite" block instead of a generic
score badge.
"""

from __future__ import annotations

from src.analyzers.message_suggester import MessageSuggester
from src.domain.entities import CommitAnalysis, PRAnalysisResult
from src.domain.enums import CheckConclusion, CommitType

__all__ = ["CommentBuilder"]


# Plain-English explanations for each issue the scorer surfaces. Keys here are
# fragments matched case-insensitively against the issue strings produced by
# the scorer; the value is the actionable advice that follows.
_ISSUE_ADVICE: dict[str, str] = {
    "not in conventional": (
        "Use the form `type(scope): description`. "
        "Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert."
    ),
    "subject too long": "Keep the subject under 72 characters; move detail to a body paragraph after a blank line.",
    "subject too short": "Subjects under 10 characters rarely describe the change. Mention the component and the action.",
    "trailing period": "Remove the trailing period from the subject — it's redundant with the line break.",
    "starts with capital": "Lowercase the first letter of the description (after the colon).",
    "imperative mood": (
        "Use imperative mood: **add**, **fix**, **remove** — not **added**, **fixed**, **removes**. "
        "Read it as 'this commit will _____'."
    ),
    "wip": "WIP/fixup/squash commits should be squashed or rebased away before merging.",
    "merge commit": "Merge commits in feature branches usually mean the branch needs a rebase against main.",
    "missing body": (
        "For `feat` and `fix` commits, add a body explaining *why* the change matters, not just what changed."
    ),
    "scope": "Adding a scope (e.g. `feat(auth):`) helps the changelog group changes by area.",
    "breaking change": (
        "Mark breaking changes with `!` after the type/scope, e.g. `feat(auth)!: drop legacy session tokens`. "
        "Add a `BREAKING CHANGE:` footer explaining the migration."
    ),
}


# Plain-English explanations for each suggestion the scorer surfaces.
_SUGGESTION_ADVICE: dict[str, str] = {
    "imperative mood": "Try starting with the verb the commit performs: 'add', 'fix', 'remove', 'rename', 'refactor'.",
    "scope": "Group related work under the same scope so changelogs read cleanly.",
    "body": "A body paragraph after a blank line explains *why* — useful for archaeology weeks later.",
}


class CommentBuilder:
    """Builds Markdown comments summarising PR commit analysis results."""

    def __init__(self) -> None:
        self._suggester = MessageSuggester()

    def build(self, result: PRAnalysisResult) -> str:
        """Build a Markdown comment showing commit analysis results."""
        sections: list[str] = [
            self._header(result),
            self._summary(result),
        ]

        # Surface each non-passing commit with its specific issues and a
        # concrete suggested rewrite — this is the heart of the comment.
        problem_commits = [c for c in result.commits if c.score < 70 or not c.is_conventional]
        if problem_commits:
            sections.append(self._per_commit_section(problem_commits))

        sections.append(self._footer(result))
        return "\n\n".join(sections)

    # ------------------------------------------------------------------ #
    # Sections
    # ------------------------------------------------------------------ #

    @staticmethod
    def _header(result: PRAnalysisResult) -> str:
        """Build a header that immediately tells the reader the verdict."""
        if result.conclusion == CheckConclusion.SUCCESS:
            opener = (
                f"All {result.total_commits} commits look good. "
                f"Average quality {result.average_score}/100 — nothing to fix."
            )
            indicator = "🟢"
        elif result.conclusion == CheckConclusion.NEUTRAL:
            opener = (
                f"{result.conventional_count} of {result.total_commits} commits follow conventional format "
                f"(avg quality {result.average_score}/100). Suggestions below are non-blocking."
            )
            indicator = "🟡"
        else:
            non_conv = result.total_commits - result.conventional_count
            opener = (
                f"{non_conv} of {result.total_commits} commits don't follow the project's commit conventions "
                f"(avg quality {result.average_score}/100). Suggested rewrites are listed below — "
                "you can apply them with `git commit --amend` or `git rebase -i`."
            )
            indicator = "🔴"

        return f"## {indicator} Commit Craft\n\n{opener}"

    @staticmethod
    def _summary(result: PRAnalysisResult) -> str:
        """A compact summary table at the top of the comment."""
        pct = round(result.conventional_ratio * 100)
        return (
            "| Metric | Value |\n"
            "| --- | --- |\n"
            f"| Total commits | {result.total_commits} |\n"
            f"| Conventional | {result.conventional_count}/{result.total_commits} ({pct}%) |\n"
            f"| Average quality | {result.average_score}/100 |\n"
            f"| Verdict | **{result.quality_level.value.title()}** |"
        )

    def _per_commit_section(self, commits: list[CommitAnalysis]) -> str:
        """Render each problem commit with specific guidance and a rewrite."""
        blocks: list[str] = ["### Per-commit feedback"]
        for commit in commits:
            blocks.append(self._commit_block(commit))
        return "\n\n".join(blocks)

    def _commit_block(self, commit: CommitAnalysis) -> str:
        """Build the block for a single problem commit."""
        sha_short = commit.sha[:7]
        verdict_line = self._verdict_line(commit)

        lines: list[str] = [
            f"#### `{sha_short}` — {commit.score}/100",
            f"> {commit.description}",
            "",
            verdict_line,
        ]

        # Issues: convert each raw issue string into an actionable bullet.
        if commit.issues:
            lines.append("\n**Why it failed:**")
            for issue in commit.issues:
                lines.append(f"- {self._explain_issue(issue)}")

        # Suggestions: similar treatment, but framed as opportunities.
        if commit.suggestions:
            lines.append("\n**Could improve:**")
            for suggestion in commit.suggestions:
                lines.append(f"- {self._explain_suggestion(suggestion)}")

        # Suggested rewrite (if any).
        suggested = self._suggester.suggest(commit.message)
        if suggested is not None:
            lines.append("\n**Suggested rewrite:**")
            lines.append(f"```\n{suggested.suggested}\n```")
            lines.append(f"_Changes: {suggested.reason}._")

        return "\n".join(lines)

    @staticmethod
    def _verdict_line(commit: CommitAnalysis) -> str:
        """One-line verdict for a commit, with type information when available."""
        if commit.is_conventional and commit.commit_type != CommitType.UNKNOWN:
            type_str = commit.commit_type.value
            if commit.scope:
                type_str += f"({commit.scope})"
            if commit.breaking:
                type_str += "!"
            return f"_Parsed as `{type_str}` — but the message has issues below._"
        return "_Not in conventional format._"

    @staticmethod
    def _explain_issue(issue: str) -> str:
        """Translate a raw scorer issue string into actionable advice."""
        lowered = issue.lower()
        for fragment, advice in _ISSUE_ADVICE.items():
            if fragment in lowered:
                return f"**{issue}.** {advice}"
        return issue

    @staticmethod
    def _explain_suggestion(suggestion: str) -> str:
        """Translate a raw scorer suggestion into a concrete tip."""
        lowered = suggestion.lower()
        for fragment, advice in _SUGGESTION_ADVICE.items():
            if fragment in lowered:
                return f"**{suggestion}** — {advice}"
        return suggestion

    @staticmethod
    def _footer(result: PRAnalysisResult) -> str:
        """Footer with a reminder of how to fix and a link back to the project."""
        if result.conclusion == CheckConclusion.SUCCESS:
            tip = ""
        else:
            tip = (
                "\n\n> **How to apply rewrites:** "
                "`git rebase -i HEAD~N` then change `pick` to `reword` for each commit you want to update. "
                "Force-push afterwards: `git push --force-with-lease`.\n"
            )
        return (
            f"{tip}\n"
            "_[Commit Craft](https://github.com/AbdullahBakir97/commit-craft) "
            "— conventional commits enforced on every PR_"
        )
