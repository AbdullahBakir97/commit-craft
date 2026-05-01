"""Tests for the per-commit, human-style Commit Craft comment builder."""

from __future__ import annotations

from typing import ClassVar

import pytest

from src.domain.entities import CommitAnalysis, PRAnalysisResult
from src.domain.enums import CheckConclusion, CommitType, QualityLevel
from src.generators.comment_builder import CommentBuilder

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


@pytest.fixture
def builder() -> CommentBuilder:
    return CommentBuilder()


def _commit(
    *,
    sha: str = "abc1234567",
    message: str = "feat(auth): add OAuth login",
    description: str = "add OAuth login",
    score: int = 95,
    is_conventional: bool = True,
    commit_type: CommitType = CommitType.FEAT,
    scope: str | None = "auth",
    breaking: bool = False,
    body: str | None = None,
    issues: list[str] | None = None,
    suggestions: list[str] | None = None,
) -> CommitAnalysis:
    return CommitAnalysis(
        sha=sha,
        message=message,
        author="user",
        is_conventional=is_conventional,
        commit_type=commit_type,
        scope=scope,
        description=description,
        body=body,
        breaking=breaking,
        score=score,
        issues=issues or [],
        suggestions=suggestions or [],
    )


def _result(
    commits: list[CommitAnalysis],
    *,
    conclusion: CheckConclusion = CheckConclusion.SUCCESS,
) -> PRAnalysisResult:
    conv = sum(1 for c in commits if c.is_conventional)
    avg = sum(c.score for c in commits) // max(len(commits), 1)
    return PRAnalysisResult(
        pr_number=1,
        total_commits=len(commits),
        conventional_count=conv,
        non_conventional_count=len(commits) - conv,
        average_score=avg,
        quality_level=QualityLevel.GOOD if avg >= 70 else QualityLevel.POOR,
        commits=commits,
        overall_issues=[],
        overall_suggestions=[],
        conclusion=conclusion,
    )


# ------------------------------------------------------------------ #
# Scenario 1: All commits good — short, positive comment
# ------------------------------------------------------------------ #


class TestAllGood:
    def test_success_uses_green_indicator(self, builder):
        result = _result([_commit(), _commit(sha="def0987654")])
        comment = builder.build(result)

        assert "🟢" in comment
        assert "All 2 commits look good" in comment

    def test_success_does_not_list_per_commit_section(self, builder):
        result = _result([_commit(), _commit(sha="def0987654")])
        comment = builder.build(result)

        assert "Per-commit feedback" not in comment

    def test_success_omits_rebase_tip(self, builder):
        result = _result([_commit()])
        comment = builder.build(result)

        assert "git rebase -i" not in comment


# ------------------------------------------------------------------ #
# Scenario 2: Some commits failing — per-commit blocks with rewrites
# ------------------------------------------------------------------ #


class TestPartialFailure:
    def test_problem_commits_get_dedicated_blocks(self, builder):
        good = _commit(sha="abc1234567")
        bad = _commit(
            sha="bad9876543",
            message="fixed stuff",
            description="fixed stuff",
            score=25,
            is_conventional=False,
            commit_type=CommitType.UNKNOWN,
            scope=None,
            issues=["Not in conventional format", "Imperative mood violated"],
        )
        result = _result([good, bad], conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)

        # Bad commit appears with its short SHA
        assert "`bad9876`" in comment
        # Good commit does NOT appear in per-commit section
        assert "`abc1234`" not in comment.split("Per-commit feedback")[1] if "Per-commit feedback" in comment else True

    def test_each_issue_has_specific_advice(self, builder):
        bad = _commit(
            sha="bad9876543",
            message="fixed stuff",
            description="fixed stuff",
            score=25,
            is_conventional=False,
            commit_type=CommitType.UNKNOWN,
            scope=None,
            issues=["Not in conventional format"],
        )
        result = _result([bad], conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)

        # Generic advice expanded into something specific
        assert "type(scope): description" in comment
        assert "Allowed types" in comment
        assert "feat, fix, docs" in comment

    def test_imperative_mood_advice_is_specific(self, builder):
        bad = _commit(
            sha="bad9876543",
            message="fix: fixed login bug",
            description="fixed login bug",
            score=60,
            is_conventional=True,
            issues=["Imperative mood: use 'fix' not 'fixed'"],
        )
        result = _result([bad], conclusion=CheckConclusion.NEUTRAL)
        comment = builder.build(result)

        assert "Use imperative mood" in comment
        assert "**add**" in comment or "**fix**" in comment

    def test_subject_too_long_advice_mentions_body(self, builder):
        long_desc = "x" * 80
        bad = _commit(
            sha="bad9876543",
            message=f"feat: {long_desc}",
            description=long_desc,
            score=60,
            issues=["Subject too long (80 chars)"],
        )
        result = _result([bad], conclusion=CheckConclusion.NEUTRAL)
        comment = builder.build(result)

        assert "72 characters" in comment
        assert "body paragraph" in comment.lower()

    def test_rewrite_section_appears_with_amend_tip(self, builder):
        bad = _commit(
            sha="bad9876543",
            message="Fixed stuff.",
            description="Fixed stuff.",
            score=25,
            is_conventional=False,
            commit_type=CommitType.UNKNOWN,
            scope=None,
            issues=["Not in conventional format"],
        )
        result = _result([bad], conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)

        # The rewrite engine produces a fix-prefixed message and the diff
        # explanation is included.
        assert "Suggested rewrite" in comment
        assert "git rebase -i" in comment


# ------------------------------------------------------------------ #
# Scenario 3: Breaking change handling
# ------------------------------------------------------------------ #


class TestBreakingChange:
    def test_breaking_commit_verdict_shows_bang(self, builder):
        bc = _commit(
            sha="bce1234567",
            message="feat(auth)!: drop legacy session tokens",
            description="drop legacy session tokens",
            score=65,  # below 70 to enter problem block
            is_conventional=True,
            commit_type=CommitType.FEAT,
            scope="auth",
            breaking=True,
            suggestions=["Add a body explaining migration"],
        )
        result = _result([bc], conclusion=CheckConclusion.NEUTRAL)
        comment = builder.build(result)

        assert "feat(auth)!" in comment


# ------------------------------------------------------------------ #
# Scenario 4: WIP / fixup commits flagged
# ------------------------------------------------------------------ #


class TestWIPCommits:
    def test_wip_commit_gets_squash_advice(self, builder):
        wip = _commit(
            sha="wip1234567",
            message="WIP: trying things",
            description="trying things",
            score=10,
            is_conventional=False,
            commit_type=CommitType.UNKNOWN,
            scope=None,
            issues=["WIP commit detected"],
        )
        result = _result([wip], conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)

        assert "squash" in comment.lower() or "rebased away" in comment.lower()


# ------------------------------------------------------------------ #
# Scenario 5: Voice quality — the bot doesn't sound like a bot
# ------------------------------------------------------------------ #


class TestVoiceQuality:
    AI_TRIGGERS: ClassVar[list[str]] = [
        "I'd be happy to",
        "hope this helps",
        "feel free to reach out",
        "let me know if you",
        "here's a breakdown",
        "delve into",
        "holistic approach",
    ]

    def test_no_ai_phrases_in_prose(self, builder):
        bad = _commit(
            sha="bad9876543",
            message="Fixed stuff.",
            description="Fixed stuff.",
            score=25,
            is_conventional=False,
            commit_type=CommitType.UNKNOWN,
            scope=None,
            issues=["Not in conventional format"],
        )
        result = _result([bad], conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)
        lowered = comment.lower()

        for phrase in self.AI_TRIGGERS:
            assert phrase.lower() not in lowered, f"Comment contains AI-style phrase '{phrase}'"

    def test_summary_uses_specific_numbers_not_vague_words(self, builder):
        commits = [
            _commit(sha="abc1234567"),
            _commit(
                sha="bad9876543",
                message="bad",
                description="bad",
                score=20,
                is_conventional=False,
                commit_type=CommitType.UNKNOWN,
                scope=None,
                issues=["Not in conventional format"],
            ),
        ]
        result = _result(commits, conclusion=CheckConclusion.FAILURE)
        comment = builder.build(result)

        # Specific numbers, not "some commits"
        assert "1 of 2 commits" in comment


# ------------------------------------------------------------------ #
# Scenario 6: Footer
# ------------------------------------------------------------------ #


class TestFooter:
    def test_footer_links_to_project(self, builder):
        result = _result([_commit()])
        comment = builder.build(result)
        assert "github.com/AbdullahBakir97/commit-craft" in comment

    def test_summary_table_present(self, builder):
        result = _result([_commit(), _commit(sha="def0987654")])
        comment = builder.build(result)

        assert "| Metric | Value |" in comment
        assert "Total commits" in comment
        assert "Conventional" in comment
        assert "Average quality" in comment
