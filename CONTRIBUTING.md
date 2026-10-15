# Contributing to Jasmin Web Panel

Thank you for considering contributing to Jasmin Web Panel! This guide will help you get started quickly and ensure a smooth contribution process.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Requesting Features](#requesting-features)
  - [Submitting Code Changes](#submitting-code-changes)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Request Guidelines](#pull-request-guidelines)

---

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold these standards. Please report unacceptable behavior to [tarek.it.eng@gmail.com](mailto:tarek.it.eng@gmail.com).

---

## How to Contribute

### Reporting Bugs

1. **Search existing issues** first to avoid duplicates.
2. Open a [Bug Report](https://github.com/101t/jasmin-web-panel/issues/new?template=bug_report.md) with:
   - Clear title describing the problem
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Environment details (OS, Python version, Docker version)
   - Relevant logs or screenshots

### Requesting Features

1. **Search existing issues/discussions** first.
2. Open a [Feature Request](https://github.com/101t/jasmin-web-panel/issues/new?template=feature_request.md) with:
   - A clear description of the feature
   - The problem it solves
   - Potential implementation ideas (optional)

### Submitting Code Changes

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-short-description
   ```
2. Make your changes following the [Coding Standards](#coding-standards).
3. **Write or update tests** for your changes.
4. Run the test suite and ensure all tests pass.
5. Submit a [Pull Request](#pull-request-guidelines).

---

## Development Setup

### Prerequisites

- Python 3.11 or 3.12
- Git
- The `telnet` client (`sudo apt install telnet`): the panel drives Jasmin's jcli console through it
- Docker & Docker Compose (recommended; also used by the integration tests)

### Local Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/jasmin-web-panel.git
cd jasmin-web-panel

# Create and activate a virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies (including dev extras)
pip install --upgrade pip wheel uv
uv pip install -r pyproject.toml --extra=dev

# Configure environment
cp sample.env .env
# For development, set in .env:
#   DEBUG=True
#   DJANGO_SETTINGS_MODULE=config.settings.dev   (SQLite, no PostgreSQL needed)
#   TELNET_HOST / TELNET_PORT pointing at a Jasmin gateway (see "Testing" for a disposable one)

# Run database migrations
python manage.py migrate

# Load sample data
python manage.py samples

# Start the development server
python manage.py runserver
```

### Docker Setup (Recommended)

```bash
cp sample.env .env
docker compose up -d
```

---

## Coding Standards

- **Python style**: Follow [PEP 8](https://peps.python.org/pep-0008/). Use `ruff` or `flake8` to check your code.
- **Django conventions**: Follow [Django's coding style](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/coding-style/).
- **Type hints**: Add type hints to new functions and methods where practical.
- **Docstrings**: Document public functions, classes, and modules.
- **Translations**: Wrap user-facing strings with `gettext_lazy` (`_("...")`).
- **Security**: Never commit secrets, credentials, or sensitive data. Use environment variables.

---

## Testing

The project uses **pytest** with **pytest-django**. There are three layers:

| Layer | Where | Needs a gateway |
|-------|-------|-----------------|
| Unit and view tests | `tests/test_*.py` | No: jcli is replaced by recorded transcripts and fakes |
| Integration tests | `tests/integration/` | Yes: a disposable Jasmin started with Docker |
| Documentation build | `mkdocs build --strict` | No |

```bash
# Unit and view tests (what most changes need)
make test
# or: DJANGO_SETTINGS_MODULE=config.settings.dev pytest tests/ -v

# Integration tests: starts Jasmin, Redis and RabbitMQ in Docker, runs the tests, removes the containers
make test_integration

# Documentation: preview with live reload, or check like CI does
make docs
mkdocs build --strict
```

CI runs all three, plus `ruff` and a Docker build, on every pull request.

When adding a new feature or fixing a bug:
- Add tests in the `tests/` directory; a bug fix should come with a test that fails without it.
- Anything that talks to jcli (`main/core/smpp/`) should have a parser or session test in
  `tests/test_jcli_parsing.py`, using output copied from a real jcli session, and an integration test when it changes
  what is sent to Jasmin.
- Changes to what a page sends or receives belong in `tests/test_manage_views.py`.

---

## Releasing

1. Set the new version in `config/version.py`, `pyproject.toml` and the image tags of `docker-compose.yml`
   (a test checks they agree), and move the CHANGELOG entries under `## X.Y.Z (date)`.
2. Merge to `master`: the **Release** workflow publishes `tarekaec/jasmin_web_panel:edge`.
3. Tag the merge commit and push the tag:

   ```bash
   git tag -a X.Y.Z -m "X.Y.Z" && git push origin X.Y.Z
   ```

   The workflow publishes `X.Y.Z`, `X.Y`, `X` and `latest` (amd64 and arm64) and creates the GitHub release from
   the CHANGELOG section.

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`

**Examples:**
```
feat(api): add rate limiting to REST endpoints
fix(submit_log): handle binary message decoding error
docs(readme): update Docker deployment instructions
chore(deps): upgrade Django to 5.2
```

---

## Pull Request Guidelines

1. **One concern per PR** — keep PRs focused on a single feature or fix.
2. **Link related issues** using keywords (`Closes #123`, `Fixes #456`).
3. **Fill in the PR template** completely.
4. **Ensure CI passes** — all automated checks must be green.
5. **Request a review** — at least one maintainer review is required before merging.
6. **Keep the branch up to date** with `main` before final review.

### PR Checklist

- [ ] My code follows the project's coding standards
- [ ] I have added/updated tests for my changes
- [ ] All existing tests pass
- [ ] I have updated documentation if needed
- [ ] The CHANGELOG has been updated (for user-facing changes)

---

## Questions?

- **Telegram**: [https://t.me/jasminwebpanel](https://t.me/jasminwebpanel)
- **GitHub Discussions**: [Start a discussion](https://github.com/101t/jasmin-web-panel/discussions)
- **Email**: [tarek.it.eng@gmail.com](mailto:tarek.it.eng@gmail.com)

Thank you for contributing! 🎉
