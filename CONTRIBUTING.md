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

- Python 3.11+
- Git
- Docker & Docker Compose (recommended)

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
# Edit .env with your local settings (SQLite works fine for development)

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

The project uses **pytest** with **pytest-django**. Run the test suite with:

```bash
# Run all tests
make test

# Or directly
DJANGO_SETTINGS_MODULE=config.settings.dev pytest tests/ -v
```

When adding a new feature or fixing a bug:
- Add tests in the `tests/` directory.
- Aim for meaningful test coverage of the new/changed code.
- Tests should be isolated and not require a live Jasmin gateway.

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
