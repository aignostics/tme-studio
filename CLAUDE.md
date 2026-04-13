# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the TME Studio repository.

## You do raise the bar, always

It is your goal to enable the contributor while insisting on highest standards at all times:

* Fully read, understand and follow this CLAUDE.md and **ALL** recursively referenced documents herein for guidance on style and conventions.
* In case of doubt apply best practices of enterprise grade software engineering.
* On every review you make or code you contribute raise the bar on engineering and operational excellence in this repository
* Do web research on any libraries, frameworks, principles or tools you are not familiar with.
* **CRITICAL: Continuously update this CLAUDE.md** when you discover new learnings, tool usage patterns, architecture insights, or efficiency improvements. This ensures you become a more effective pair programmer over time. Document what you learned, why it matters, and how to apply it.

### Code Quality Principles

**ALWAYS follow these principles when writing ANY code, especially tests:**

1. **SonarQube Rules Compliance**: All code must comply with SonarQube rules before considering it complete.
   * **S1192 (String Duplication)**: Extract repeated string literals (duplicated 3+ times) into module-level constants
   * Define constants at the top of the file after imports with descriptive names (e.g., `EXPECTED_TIMESTAMP_PREFIX`, `API_ENDPOINT_BUCKET_WRITE`)
   * This applies to **test files** as well - tests are production code and must meet the same quality standards

2. **DRY Principle (Don't Repeat Yourself)**: Never duplicate code or string literals
   * If you find yourself copying the same string literal multiple times, extract it to a constant
   * If you find yourself copying test logic, extract it to a helper function or fixture
   * Even in tests: constants improve maintainability and reduce typo risks

3. **Raise the Bar on Clean Code**: Every commit should improve code quality
   * Run `mise run lint` AFTER writing code to catch issues immediately
   * Fix all SonarQube issues before considering work complete
   * Never generate code that violates quality rules - prevent technical debt at the source

**Why this matters**: SonarQube failures block CI/CD pipelines. Code that doesn't meet quality gates cannot be merged. By following these principles proactively, we prevent wasted cycles and maintain the high quality standards this project demands.

### Development Tools

* uv, python and development dependencies are already installed
* Use `uv sync --all-extras` to install any missing dependencies
* Use `pytest ...` to run tests
* Use `mise run lint` to check code style and types
* Use `mise run test_unit`, `mise run test_integration`, `mise run test_e2e` for testing
* Use `mise run audit` for security audits

### Validation Requirements

If you write code yourself, it is a strict requirement to validate before completion:

* **ALWAYS run `mise run lint` first** - Linting must pass before running tests
* Unit, integration and e2e test suites must pass
* Auditing must pass

## Project Overview

**TME Studio** - A toolkit to explore the Aignostics OpenTME dataset.

## Python Version

**CRITICAL**: Requires Python 3.11+ (`>=3.11`). Specified in `.python-version`, CI tests against 3.11-3.12.

## Testing Strategy

**Every test MUST have at least one marker** (`unit`, `integration`, or `e2e`). Tests without markers won't run in CI.

```bash
mise run test_unit              # Fast, isolated
mise run test_integration       # Real local services
mise run test_e2e               # End-to-end
```

**Coverage**: Goal 100%, minimum 85%.

See [tests/CLAUDE.md](tests/CLAUDE.md) for detailed testing guidance including markers, fixtures, parallelization, and best practices.

## Development Workflow

### Initial Setup

```bash
gh auth login
gh repo clone aignostics/tme-studio
cd tme-studio
mise trust
gh auth setup-git
mise run install          # uv sync + pre-commit hooks
mise run lint && mise run test_unit
```

### Development Cycle

```bash
git checkout -b feat/my-feature

# Make changes, then validate
mise run lint             # MUST pass before tests
mise run test_unit
mise run test_integration

# Full validation before PR
mise run all              # lint + test + docs + audit

git commit -m "feat(module): description"
git push origin feat/my-feature
```

## Package Management & Build

**uv** is the package manager:

```bash
uv sync --all-extras          # Install all dependencies
uv add package-name           # Add dependency
uv build                      # Build wheel and sdist
```

**Configuration**: See `pyproject.toml` for:
* `requires-python = ">=3.11"`
* `dependencies` - Runtime
* `dependency-groups.dev` - Development tools

**Build system**: Hatchling

## mise & Nox

**Primary tasks**:
```bash
mise run all              # Run all checks (lint + test + docs + audit)
mise run install          # Setup dev environment
mise run clean            # Remove artifacts
mise run lint             # Ruff
mise run test_*           # Various test suites
mise run docs             # Build documentation
mise run audit            # Security and license checks
```

**Nox sessions**: `lint`, `test`, `docs`, `audit` - See `noxfile.py` for details.

**Pre-commit hooks**: Auto-format with ruff, detect secrets. Run manually: `mise run pre_commit_run_all`

## Code Standards

**Code style**: Ruff handles all formatting and linting (120 char limit, Google-style docstrings). See `pyproject.toml` for configuration.

## Tooling Configuration

All tool configuration lives in these files (single source of truth):
* `pyproject.toml` - Ruff, pytest, coverage, commitizen
* `.pre-commit-config.yaml` - Pre-commit hooks
* `noxfile.py` - Test and build automation
* `.license-types-allowed` - License compliance

## CI/CD Integration

**Workflows**: `ci-cd.yml` (main pipeline), reusable workflows for lint, test, audit, deploy.

**Tests run on**: Python 3.11-3.12, Linux (ubuntu-latest)

See [.github/CLAUDE.md](.github/CLAUDE.md) for complete CI/CD documentation.



## Documentation

### Primary docs
* [README.md](README.md) - Quick start
* [CODE_STYLE.md](CODE_STYLE.md) - Code style guide
* [SECURITY.md](SECURITY.md) - Security policy

### Auto-generated
* [ATTRIBUTIONS.md](ATTRIBUTIONS.md) - Third-party licenses

## Quick Reference

```bash
# Get started
mise run install && mise run lint && mise run test_unit

# Development loop
mise run lint && mise run test_unit && mise run test_integration

# Full validation before PR
mise run all  # runs lint + test + docs + audit

# Version bump and release
cz bump [patch|minor|major]
```

---

*Built with operational excellence practices.*
