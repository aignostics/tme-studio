# CLAUDE.md - CI/CD & GitHub Actions Guide

This file provides guidance for Claude Code and engineers working with the CI/CD infrastructure and GitHub Actions workflows in TME Studio.

## Overview

This project uses a **comprehensive CI/CD pipeline** built on GitHub Actions with:

* **Reusable workflow architecture** (entry points + reusable workflows)
* **Comprehensive quality gates** (lint, audit, test)
* **Claude Code integration** (automated PR reviews)
* **Scheduled security auditing**

## Workflow Architecture

```text
+-------------------------------------------------------------+
|                 ci-cd.yml (Main Orchestrator)                |
|      Triggered on: push, PR, workflow_dispatch               |
+-------------------------------------------------------------+
|                                                              |
|  +--------+  +-------+  +--------+                          |
|  |  Lint  |  | Audit |  |  Test  |                          |
|  | (5 min)|  |(3 min)|  |(15 min)|                          |
|  +---+----+  +---+---+  +---+----+                          |
|      |           |          |                                |
|      +-----------+----------+                                |
|                  |                                           |
|         Quality Gate Pass                                    |
+-------------------------------------------------------------+

+-----------------------------------------------------------+
|                    Parallel Entry Points                   |
+-----------------------------------------------------------+
|  claude-code-*.yml        -> PR reviews                   |
|  codeql-scheduled.yml     -> Security scanning (weekly)   |
|  scheduled-audit-*.yml    -> Security audit               |
|  git-conventions.yml      -> Commit message validation    |
|  labels-sync.yml          -> GitHub labels management     |
+-----------------------------------------------------------+
```

## Main CI/CD Pipeline (ci-cd.yml)

**Purpose**: Orchestrate quality checks

**Triggers**:

* `pull_request` to `main` - Opens PR, updates PR, reopens PR
* `push` to `main` or `release/v*` branches
* `workflow_dispatch` - Manual trigger

**Concurrency**:

```yaml
group: cicd-${{ github.ref }}
cancel-in-progress: true
```

Cancels in-progress runs for same branch

**Skip Conditions**:

* Commit message contains `[skip ci]`

### Quality Gate Jobs

#### `lint`

**Workflow**: `_lint.yml`

**Duration**: ~5 minutes

**What it does**:

* Ruff format check
* Ruff lint check

**Fail conditions**: Any check fails

#### `audit`

**Workflow**: `_audit.yml`

**Duration**: ~3 minutes

**What it does**:

* `pip-audit` for vulnerability scanning
* `pip-licenses` for license compliance
* SBOM generation (CycloneDX + SPDX)

**Fail conditions**: Vulnerabilities found or non-compliant licenses

#### `test`

**Workflow**: `_test.yml`

**Duration**: ~15 minutes

**What it does**:

* Unit tests (parallel)
* Integration tests (parallel)
* E2E tests
* Coverage reporting (Codecov + SonarCloud)

**Secrets required**:

* `CODECOV_TOKEN`
* `SONAR_TOKEN`

## Reusable Workflows

### `_lint.yml`

**Purpose**: Code quality checks

**Steps**:

1. Checkout code
2. Setup Python + uv
3. Run `mise run lint`:
   * `ruff format --check`
   * `ruff check`

**Exit on**: First failure

### `_audit.yml`

**Purpose**: Security and license compliance

**Steps**:

1. Setup environment
2. Run `mise run audit`:
   * `pip-audit` with JSON output
   * `pip-licenses` with allowed list from `.license-types-allowed`
   * SBOM generation via Trivy

**Artifacts**:

* `reports/vulnerabilities.json`
* `reports/licenses.csv`
* `reports/sbom.json` (CycloneDX)
* `reports/sbom.spdx` (SPDX)

### `_test.yml`

**Purpose**: Run test suite with coverage

**Note**: This workflow does not create GitHub deployment environments, as it is designed for library projects.

**Steps**:

1. Setup environment (Python, uv)
2. Run test categories:
   * `mise run test_unit`
   * `mise run test_integration`
   * `mise run test_e2e`
3. Upload coverage to Codecov and SonarCloud

## Claude Code Integration

### `claude-code-automation-pr-review.yml`

**Purpose**: Automated PR code review by Claude

**Trigger**: PR opened/synchronized (excluding bot PRs)

**Review focus**:

* Code quality
* Test coverage
* Security
* Adherence to CLAUDE.md guidelines

**Secrets required**:

* `ANTHROPIC_API_KEY`

## Git Conventions

### `git-conventions.yml`

**Purpose**: Validate branch names, commit messages, and PR titles

**Trigger**: PR opened/edited/synchronized/reopened

**Checks**:

* Branch name format (e.g., `feat/description`, `fix/description`)
* Conventional commit format for all PR commits
* PR title format (for squash merges)

**Conventional commit types**:

* `feat:` - New feature
* `fix:` - Bug fix
* `docs:` - Documentation
* `refactor:` - Code refactoring
* `test:` - Test changes
* `chore:` - Maintenance
* `ci:` - CI/CD changes

## Labels Management

### `labels-sync.yml`

**Purpose**: Synchronize GitHub labels from `.github/labels.yml`

**Trigger**: Push to main, manual

**Features**:

* Creates missing labels
* Updates existing labels
* Removes unlisted labels (optional)

## CodeQL Security Scanning

### `codeql-scheduled.yml`

**Purpose**: Static analysis for security vulnerabilities

**Trigger**: Weekly schedule (Tuesdays at 3:22 AM UTC)

**What it does**:

* Analyzes Python code for security vulnerabilities
* Analyzes GitHub Actions workflow files for misconfigurations
* Reports findings to GitHub Security tab

**Languages scanned**:

* Python (build-mode: none)
* GitHub Actions (build-mode: none)

**No secrets required**: Uses built-in GitHub token

### `_codeql.yml`

**Purpose**: Reusable CodeQL analysis workflow

**Steps**:

1. Checkout code
2. Initialize CodeQL
3. Autobuild (minimal for Python)
4. Perform analysis

**Permissions**:

* `actions: read`
* `contents: read`
* `packages: read`
* `security-events: write`

## Secrets Management

**Required GitHub Secrets**:

**Code Quality**:

* `CODECOV_TOKEN` - Codecov coverage reporting
* `SONAR_TOKEN` - SonarCloud analysis

**Claude Code**:

* `ANTHROPIC_API_KEY` - Claude API access

## Debugging CI Failures

### Lint Failures

**Reproduce locally**:

```bash
mise run lint
```

**Common issues**:

* Formatting: `ruff format .`
* Linting: `ruff check . --fix`

### Test Failures

**Reproduce locally**:

```bash
mise run test_unit
mise run test_integration
mise run test_e2e
```

**Check CI logs**:

1. Go to Actions tab
2. Select failed workflow
3. Expand failed test job
4. Review pytest output

### Secret Issues

**Problem**: Missing or invalid secrets

**Symptoms**:

* Authentication failures
* "Secret not found" errors

**Solution**:

1. Verify secret exists in GitHub Settings > Secrets
2. Check secret name matches workflow reference
3. Verify secret value is correct

## Performance & Optimization

### Workflow Duration

| Job | Duration | Notes |
|-----|----------|-------|
| Lint | ~5 min | Ruff |
| Audit | ~3 min | pip-audit + licenses + SBOM |
| Test | ~15 min | Unit + integration + e2e |
| Full pipeline | ~25 min | All quality gates |

### Caching

* **uv dependencies**: Cached via `astral-sh/setup-uv` action
* **Docker layers**: Cached by build system

### Parallelization

* **Test matrix**: Python 3.11-3.12
* **Test parallelization**: Via pytest-xdist
* **Job parallelization**: Lint, audit, test run in parallel

## Best Practices

1. **Always add conventional commit messages** for changelog generation
2. **Use PR labels** to control pipeline behavior (skip long tests, etc.)
3. **Test locally first** before pushing (`mise run lint`, `mise run test`)
4. **Keep PRs small** for faster reviews
5. **Document breaking changes** in PR description
6. **Run full test suite** before merging to main

---

*Built with operational excellence practices.*
