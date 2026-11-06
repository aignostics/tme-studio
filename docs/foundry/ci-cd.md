> [!NOTE]
> Maintained by [foundry-python](https://github.com/aignostics/foundry-python) and updated by `mise run update_from_template`. Changed it? [Send it upstream](README.md#changed-a-template-file-send-it-upstream).

# CI/CD Workflows

## Main Workflows

| Workflow | Triggers | Purpose |
|----------|----------|---------|
| `ci-cd.yml` | PR, push to `main`, version tags | lint → audit → test → publish |
| `git-conventions.yml` | PR | Validates commit messages and PR titles |
| `mise-lock-sync.yml` | PR (mise config changes) | Regenerates `mise.lock` on Linux and commits it to the PR branch (`mise lock` output depends on the host OS) |
| `lint-workflows.yml` | PR (workflow or action changes) | actionlint, and pinact: every action pinned to a SHA with a version comment |
| `labels-sync.yml` | Push to `main` | Syncs GitHub labels from `.github/labels.yml` |
| `claude-code-automation-pr-review.yml` | PR with `claude` label | AI PR review |
| `audit-scheduled.yml` | Daily 06:00 UTC | Security audit with BetterStack heartbeat |
| `test-scheduled-staging-daily.yml`, `test-scheduled-production-daily.yml` | Daily 12:00 UTC | `scheduled` tests against staging / production |
| `bump.yml` | Manual (`mise run bump`) | Release: requires green CI on the commit → bump, tag, push |

## Reusable Workflows

| Workflow | Purpose |
|----------|---------|
| `_lint.yml` | Ruff, Pyrefly, deptry, via the git hooks |
| `_test.yml` | Unit, integration, E2E tests; coverage floor; SonarCloud scan (quality gate blocks pull requests) |
| `_audit.yml` | Security scanning and SBOM generation. On PRs it scans the base branch too and fails only on findings the PR adds; on `main` it fails on any finding |
| `_package-publish.yml` | Build, audit, publish to Artifact Registry, GitHub release |

## GCP Authentication

All CI workflows authenticate to GCP using org-level Workload Identity Federation (WIF) variables — no per-repo secrets required.

| Variable | Pool | Used by |
|----------|------|---------|
| `vars.WIF_PROVIDER_DEV` | `github-dev` | All static CI workflows (lint, test, audit, bump, publish) |
| `vars.WIF_PROVIDER_TEST` | `github-test` | Scheduled tests against `test` environment |
| `vars.WIF_PROVIDER_STAGE` | `github-stage` | Scheduled tests against `staging` environment |
| `vars.WIF_PROVIDER_PROD` | `github-prod` | Scheduled tests against `production` environment |

`Setup Dev Environment` mints the private-registry token once and masks it before mise starts, so job logs show it as `***`.

GAR access is granted via the `python_gar_access` GitHub custom property on your repo:
- `python-gar-reader` (org-wide default) — read-only access for `uv sync`
- `python-gar-writer` — write access for `uv publish` (library repos that publish to GAR)

To request `python-gar-writer`, ask the Platform Engineering team in [#support-platform-engineering](https://aignostics.slack.com/archives/C08SYE0JV3M).

## Skipping Tests in CI

Add to the commit message or as a PR label. The coverage floor is not checked when a suite is skipped.

| Skip Marker | Effect |
|-------------|--------|
| `skip:test:unit` | Skip unit tests |
| `skip:test:integration` | Skip integration tests |
| `skip:test:e2e` | Skip E2E tests |
| `skip:test:all` | Skip all tests |

---

## Versioning & Releases

The `main` branch protection rule must include **`aignostics-release-bot`** in the bypass list (set to **"Always allow"**). The release bot pushes version-bump commits directly to `main` during automated releases — without this bypass, releases will fail.

### Creating a Release

```shell
mise run bump                  # bump type from commits since the last tag
```

Pass [`cz bump` arguments](https://commitizen-tools.github.io/commitizen/bump/) after `--`:

```shell
# Explicit increment type
mise run bump -- --increment patch
mise run bump -- --increment minor
mise run bump -- --increment major

# Pre-release versions
mise run bump -- --prerelease rc           # e.g., 1.0.0 → 1.0.1-rc.0
mise run bump -- --increment major --prerelease rc  # e.g., 1.0.0 → 2.0.0-rc.0
```

`mise run bump` triggers `bump.yml`, which:
1. Requires a green `ci-cd.yml` run on the commit it releases
2. Bumps version using Commitizen and updates CHANGELOG.md
3. Creates git tag
4. Pushes to remote (triggers publish workflow). If `main` moved on meanwhile, the push is rejected; re-run

### Conventional Commits

Commit messages and PR titles are checked by Commitizen (`cz_conventional_commits`). The [Conventional Commits spec](https://www.conventionalcommits.org/en/v1.0.0/) defines only `feat`, `fix` and breaking changes; the other types are Commitizen's: `build`, `bump`, `chore`, `ci`, `docs`, `perf`, `refactor`, `revert`, `style`, `test`.

| Commit | Version bump | Example |
|--------|--------------|---------|
| `feat` | Minor | `feat(api): add user endpoint` |
| `fix`, `refactor`, `perf` | Patch | `fix(auth): handle expired tokens` |
| `!` or `BREAKING CHANGE:` footer | Major (Minor while the version is `0.x`) | `feat!: redesign API response format` |
| any other type | None | `docs: update README` |

The changelog lists `feat`, `fix`, `refactor`, `perf`, `chore` and `docs` (`change_type_map` in `pyproject.toml`).

---

## Release Task Reference

| Task | Description |
|------|-------------|
| `mise run bump` | Trigger the release workflow (accepts [cz bump arguments](https://commitizen-tools.github.io/commitizen/bump/)) |
| `mise run update_from_template` | Update project from the latest foundry-python template |

---

## Keeping Updated

```shell
mise run update_from_template
```

Merges the latest template release into the files foundry-python owns (everything it generated except `README.md`, `CHANGELOG.md` and `logo.png`), then runs lint and audit. Resolve any `*.rej` files it leaves.

`copier update` targets the latest release **tag**, not `main`: a merged template change arrives once it is released.

Conflicts every update usually mean a local edit to a template file. [Send it upstream](README.md#changed-a-template-file-send-it-upstream) and the conflict goes away.
