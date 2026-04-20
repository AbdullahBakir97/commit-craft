"""Tests for the MessageScorer."""

from __future__ import annotations

import pytest

from src.analyzers.message_scorer import MessageScorer


@pytest.fixture()
def scorer() -> MessageScorer:
    """Provide a scorer instance."""
    return MessageScorer()


class TestMessageScorer:
    """Tests for commit message scoring logic."""

    def test_perfect_score(self, scorer: MessageScorer) -> None:
        """A well-formed conventional commit should score high."""
        score, issues, suggestions = scorer.score("feat(auth): add OAuth2 login with Google provider")
        assert score >= 80
        assert len(issues) == 0

    def test_non_conventional_loses_points(self, scorer: MessageScorer) -> None:
        """A non-conventional message should lose the format points."""
        score, issues, _ = scorer.score("add login page")
        assert score < 70
        assert any("conventional" in i.lower() for i in issues)

    def test_short_description_penalised(self, scorer: MessageScorer) -> None:
        """Very short descriptions should be penalised."""
        score, issues, _ = scorer.score("feat: fix")
        assert any("short" in i.lower() for i in issues)

    def test_long_description_penalised(self, scorer: MessageScorer) -> None:
        """Descriptions over 72 chars should be penalised."""
        long_desc = "a" * 80
        score, issues, _ = scorer.score(f"feat: {long_desc}")
        assert any("72" in i for i in issues)

    def test_uppercase_start_penalised(self, scorer: MessageScorer) -> None:
        """Descriptions starting with uppercase should be penalised."""
        score, issues, _ = scorer.score("feat: Add login page to the application")
        assert any("lowercase" in i.lower() for i in issues)

    def test_trailing_period_penalised(self, scorer: MessageScorer) -> None:
        """Descriptions ending with a period should be penalised."""
        score, issues, _ = scorer.score("feat: add login page.")
        assert any("period" in i.lower() for i in issues)

    def test_wip_penalised(self, scorer: MessageScorer) -> None:
        """WIP commits should be penalised."""
        score, issues, _ = scorer.score("WIP save progress")
        assert any("WIP" in i for i in issues)
        assert score < 50

    def test_fixup_penalised(self, scorer: MessageScorer) -> None:
        """fixup! commits should be penalised."""
        score, issues, _ = scorer.score("fixup! previous commit")
        assert any("WIP" in i or "fixup" in i.lower() for i in issues)

    def test_merge_commit_penalised(self, scorer: MessageScorer) -> None:
        """Merge commits should be penalised."""
        score, issues, _ = scorer.score("Merge branch 'main' into feature/x")
        assert any("merge" in i.lower() for i in issues)

    def test_imperative_mood_rewarded(self, scorer: MessageScorer) -> None:
        """Messages starting with an imperative verb should score higher."""
        score_good, _, _ = scorer.score("feat: add login page")
        score_bad, _, _ = scorer.score("feat: added login page")
        assert score_good > score_bad

    def test_scope_bonus(self, scorer: MessageScorer) -> None:
        """Messages with a scope should score higher than without."""
        score_with, _, _ = scorer.score("feat(auth): add login endpoint")
        score_without, _, _ = scorer.score("feat: add login endpoint")
        assert score_with > score_without

    def test_score_clamped_to_100(self, scorer: MessageScorer) -> None:
        """Score should never exceed 100."""
        score, _, _ = scorer.score(
            "feat(auth)!: add OAuth2 login with Google provider\n\nThis implements the full OAuth2 flow."
        )
        assert score <= 100

    def test_score_minimum_zero(self, scorer: MessageScorer) -> None:
        """Score should never go below 0."""
        score, _, _ = scorer.score(".")
        assert score >= 0

    @pytest.mark.parametrize(
        "message",
        [
            "Fixed stuff",
            "WIP",
            "update",
            ".",
            "asdf",
        ],
    )
    def test_bad_messages_score_low(self, scorer: MessageScorer, message: str) -> None:
        """Bad messages should score below 50."""
        score, _, _ = scorer.score(message)
        assert score < 50

    @pytest.mark.parametrize(
        "message",
        [
            "feat(auth): add OAuth2 login with Google provider",
            "fix(api): resolve null pointer on empty request body",
            "docs: update README with installation instructions",
        ],
    )
    def test_good_messages_score_high(self, scorer: MessageScorer, message: str) -> None:
        """Good conventional messages should score at least 70."""
        score, _, _ = scorer.score(message)
        assert score >= 70
