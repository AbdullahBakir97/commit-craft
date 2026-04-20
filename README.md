# Commit Craft

[![CI](https://github.com/AbdullahBakir97/commit-craft/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdullahBakir97/commit-craft/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Automated conventional commit message quality enforcement for GitHub PRs.**

---

## The Problem

Messy commit histories make changelogs impossible to generate, release notes painful to write, and code archaeology a nightmare. Teams waste time debating commit message style in code reviews instead of focusing on the code itself.

## The Solution

Commit Craft is a GitHub App that automatically analyzes every commit in a pull request, scores message quality against the [Conventional Commits](https://www.conventionalcommits.org/) specification, and reports results via GitHub Checks. No more manual style policing -- let the bot handle it.

## Features

- **Conventional Commit Parsing** -- validates `type(scope): description` format
- **Quality Scoring** -- 0-100 score based on length, imperative mood, casing, and more
- **Smart Suggestions** -- auto-generates improved messages for non-conforming commits
- **GitHub Checks** -- pass/fail status directly on PRs with detailed breakdown
- **PR Comments** -- rich Markdown summary with per-commit analysis
- **Changelog Generation** -- group conventional commits by type automatically
- **Per-Repo Config** -- customise rules via `.github/commit-craft.yml`

## Example Output

**Good commit:**
```
feat(auth): add OAuth2 login with Google provider
```
Score: 95/100 -- Conventional format, imperative mood, descriptive, scoped.

**Bad commit:**
```
Fixed stuff
```
Score: 25/100 -- No conventional type, vague description, past tense.

**Suggested fix:**
```
fix: resolve the reported issue
```

## Configuration

Create `.github/commit-craft.yml` in your repository:

```yaml
enabled: true
require_conventional: true
min_score: 60
action: check  # check | comment | request-changes | block
allowed_types:
  - feat
  - fix
  - docs
  - style
  - refactor
  - perf
  - test
  - build
  - ci
  - chore
  - revert
max_subject_length: 72
require_scope: false
require_body: false
ignore_merge_commits: true
ignore_revert_commits: true
```

All fields are optional and fall back to sensible defaults.

## Getting Started

### 1. Install the GitHub App

Install Commit Craft on your repositories from the GitHub Marketplace.

### 2. Configure (optional)

Add a `.github/commit-craft.yml` file to customise the rules for your repository.

### 3. Open a PR

Commit Craft will automatically analyse the commits and report results as a GitHub Check.

### Local Development

```bash
# Clone the repository
git clone https://github.com/AbdullahBakir97/commit-craft.git
cd commit-craft

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env with your GitHub App credentials

# Run the server
python -m src.main
```

### Running Tests

```bash
pytest -v
```

### API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/webhook` | GitHub webhook receiver |
| `POST` | `/api/v1/analyze` | Analyse a single commit message (demo) |
| `GET` | `/health` | Health check |
| `GET` | `/dashboard` | Interactive dashboard |

## Tech Stack

- **Python 3.12+** with full type hints
- **FastAPI** for the async API layer
- **Pydantic** for validation and configuration
- **httpx** for async GitHub API calls
- **PyJWT** for GitHub App authentication
- **PyYAML** for per-repo config parsing

## Architecture

```
src/
  analyzers/       # Commit parsing, scoring, suggestion, PR analysis
  generators/      # Comment, check run, and changelog builders
  infrastructure/  # GitHub client, auth, webhook, config loading
  application/     # Orchestrator and webhook handler
  api/             # FastAPI routes, middleware, schemas
  config/          # Settings and logging
  container.py     # Dependency injection
  main.py          # Entry point
```

## License

[MIT](LICENSE) -- Abdullah Bakir, 2026
