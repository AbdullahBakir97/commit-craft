"""Shared test fixtures for Commit Craft."""

from __future__ import annotations

import pytest


@pytest.fixture()
def good_conventional_messages() -> list[str]:
    """Well-formed conventional commit messages."""
    return [
        "feat(auth): add OAuth2 login with Google provider",
        "fix(api): resolve null pointer on empty request body",
        "docs: update README with installation instructions",
        "refactor(db): extract query builder into separate module",
        "test(auth): add unit tests for JWT validation",
        "perf(cache): reduce Redis round-trips by batching keys",
        "chore: bump dependencies to latest versions",
        "ci: add GitHub Actions workflow for linting",
        "build: switch from setuptools to hatchling",
        "style: apply black formatting to all modules",
        "feat!: drop Python 3.10 support",
        "feat(parser): add support for multi-line commit bodies\n\nThis change allows the parser to extract body content\nfrom commits that follow the conventional format.",
    ]


@pytest.fixture()
def bad_commit_messages() -> list[str]:
    """Commit messages that violate conventional commit rules."""
    return [
        "Fixed stuff",
        "WIP",
        "update",
        "Merge branch 'main' into feature/login",
        "fixup! previous commit",
        "Changed the thing that was broken and also updated some other stuff that needed updating too for reasons",
        "YOLO deploy.",
        "asdf",
        ".",
        "Added new feature for the login page",
    ]


@pytest.fixture()
def mixed_pr_commits() -> list[dict[str, str]]:
    """A realistic PR with a mix of good and bad commits."""
    return [
        {
            "sha": "abc1234567890",
            "message": "feat(auth): add OAuth2 login",
            "author": "Alice",
        },
        {
            "sha": "def4567890123",
            "message": "fix typo",
            "author": "Alice",
        },
        {
            "sha": "ghi7890123456",
            "message": "fix(auth): resolve redirect loop on logout",
            "author": "Alice",
        },
        {
            "sha": "jkl0123456789",
            "message": "Merge branch 'main' into feature/auth",
            "author": "GitHub",
        },
        {
            "sha": "mno3456789012",
            "message": "WIP save progress",
            "author": "Alice",
        },
    ]


@pytest.fixture()
def sample_commit_dict() -> dict[str, str]:
    """A single well-formed commit dict."""
    return {
        "sha": "abc1234567890",
        "message": "feat(auth): add OAuth2 login with Google provider",
        "author": "Alice",
    }
