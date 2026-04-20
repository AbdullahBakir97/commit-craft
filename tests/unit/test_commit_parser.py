"""Tests for the ConventionalCommitParser."""

from __future__ import annotations

import pytest

from src.analyzers.commit_parser import ConventionalCommitParser
from src.domain.enums import CommitType


@pytest.fixture()
def parser() -> ConventionalCommitParser:
    """Provide a parser instance."""
    return ConventionalCommitParser()


class TestConventionalCommitParser:
    """Tests for parsing conventional commit messages."""

    def test_parse_simple_feat(self, parser: ConventionalCommitParser) -> None:
        """A simple feat commit should be parsed correctly."""
        result = parser.parse("feat: add login page")
        assert result["is_conventional"] is True
        assert result["type"] == CommitType.FEAT
        assert result["scope"] is None
        assert result["description"] == "add login page"
        assert result["breaking"] is False
        assert result["body"] is None

    def test_parse_with_scope(self, parser: ConventionalCommitParser) -> None:
        """A commit with scope should extract it correctly."""
        result = parser.parse("fix(auth): resolve token expiry")
        assert result["is_conventional"] is True
        assert result["type"] == CommitType.FIX
        assert result["scope"] == "auth"
        assert result["description"] == "resolve token expiry"

    def test_parse_breaking_change(self, parser: ConventionalCommitParser) -> None:
        """A breaking change marker should be detected."""
        result = parser.parse("feat!: drop legacy API")
        assert result["is_conventional"] is True
        assert result["breaking"] is True

    def test_parse_breaking_change_in_body(self, parser: ConventionalCommitParser) -> None:
        """BREAKING CHANGE in body should be detected."""
        result = parser.parse("feat: new auth\n\nBREAKING CHANGE: removes v1 endpoints")
        assert result["is_conventional"] is True
        assert result["breaking"] is True

    def test_parse_with_body(self, parser: ConventionalCommitParser) -> None:
        """Multi-line messages should extract the body."""
        result = parser.parse("docs: update readme\n\nAdded installation instructions.")
        assert result["body"] == "Added installation instructions."

    def test_parse_non_conventional(self, parser: ConventionalCommitParser) -> None:
        """Non-conventional messages should return is_conventional=False."""
        result = parser.parse("Fixed the login bug")
        assert result["is_conventional"] is False
        assert result["type"] == CommitType.UNKNOWN
        assert result["description"] == "Fixed the login bug"

    def test_parse_all_types(self, parser: ConventionalCommitParser) -> None:
        """All standard types should be recognized."""
        types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
        for t in types:
            result = parser.parse(f"{t}: do something")
            assert result["is_conventional"] is True
            assert result["type"] == CommitType(t)

    def test_parse_case_insensitive(self, parser: ConventionalCommitParser) -> None:
        """Type matching should be case-insensitive."""
        result = parser.parse("FEAT: add feature")
        assert result["is_conventional"] is True
        assert result["type"] == CommitType.FEAT

    def test_parse_empty_message(self, parser: ConventionalCommitParser) -> None:
        """Empty messages should be handled gracefully."""
        result = parser.parse("")
        assert result["is_conventional"] is False

    def test_parse_merge_commit(self, parser: ConventionalCommitParser) -> None:
        """Merge commits are not conventional."""
        result = parser.parse("Merge branch 'main' into feature/x")
        assert result["is_conventional"] is False

    @pytest.mark.parametrize(
        "message",
        [
            "feat: add login page",
            "fix(api): resolve null pointer",
            "docs: update README",
            "refactor(db): extract query builder",
        ],
    )
    def test_parse_good_messages(self, parser: ConventionalCommitParser, message: str) -> None:
        """Good conventional messages should all parse as conventional."""
        result = parser.parse(message)
        assert result["is_conventional"] is True
