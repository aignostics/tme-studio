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
|  claude-code-*.yml        -> PR reviews (label-gated)     |
|  audit-scheduled.yml      -> Security audit               |
|  git-conventions.yml      -> Commit/PR title validation   |
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
group: ${{ github.workflow }}-${{ github.ref_name }}-${{ github.event.pull_request.number || github.sha }}
cancel-in-progress: true
```

Cancels in-progress runs for same branch/PR

**Skip Conditions**:

* Commit message contains `[skip ci]`

### Quality Gate Jobs

#### `lint`

**Workflow**: `_lint.yml`

**Duration**: ~5 minutes

**What it does**:

* Runs `mise run pre_commit_run_all` (ruff format, ruff lint, pyrefly, secret detection)

**Fail conditions**: Any check fails

#### `audit`

**Workflow**: `_audit.yml`

**Duration**: ~3 minutes

**What it does**:

* `trivy` for vulnerability scanning, license compliance, and SBOM generation
* SBOM generation (CycloneDX + SPDX)

**Fail conditions**: Vulnerabilities found or non-compliant licenses

#### `test`

**Workflow**: `_test.yml`

**Duration**: ~15 minutes

**What it does**:

* Unit tests (parallel)
* Integration tests (parallel)
* E2E tests
* Coverage reporting (SonarQube)

**Secrets required**:

* `SONAR_TOKEN`

## Reusable Workflows

### `_lint.yml`

**Purpose**: Code quality checks

**Steps**:

1. Checkout code
2. Setup Python + uv
3. Run `mise run pre_commit_run_all`

**Exit on**: First failure

### `_audit.yml`

**Purpose**: Security and license compliance

**Steps**:

1. Setup environment
2. Run `mise run audit`:
   * `trivy` vulnerability scan with `.trivyignore` for known false positives
   * `trivy` license scan with allowed list from `.license-types-allowed`
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
   * `mise run test:unit`
   * `mise run test:integration`
   * `mise run test:e2e`
3. Upload coverage to Codecov and SonarQube

## Claude Code Integration

### `claude-code-automation-pr-review.yml`

**Purpose**: Automated PR code review by Claude

**Trigger**: PR events (opened, synchronize, labeled, etc.) when the `claude` label is applied; excludes dependabot and renovate bots

**Review focus**:

* Code quality
* Test coverage
* Security
* Adherence to CLAUDE.md guidelines

**Secrets required**:

* `ANTHROPIC_API_KEY`

## Git Conventions

### `git-conventions.yml`

**Purpose**: Validate commit messages and PR titles

**Trigger**: PR opened/edited/synchronized/reopened

**Checks**:

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

## Secrets Management

**Required GitHub Secrets**:

**Code Quality**:

* `SONAR_TOKEN` - SonarQube analysis

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
* Type errors: Check Pyrefly output

### Test Failures

**Reproduce locally**:

```bash
mise run test:unit
mise run test:integration
mise run test:e2e
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
| Lint | ~5 min | Ruff + Pyrefly (via pre-commit) |
| Audit | ~3 min | trivy (vulns + licenses + SBOM) |
| Test | ~15 min | Unit + integration + e2e |
| Full pipeline | ~25 min | All quality gates |

### Caching

* **uv dependencies**: Cached via `astral-sh/setup-uv` action
* **Docker layers**: Cached by build system

### Parallelization

* **Test parallelization**: Via pytest-xdist (single Python version from `.python-version`)
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
