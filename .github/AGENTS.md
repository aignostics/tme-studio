# AGENTS.md — CI/CD

Root guidance: [../AGENTS.md](../AGENTS.md)

## Structure

`ci-cd.yml` is the only entry point for quality gates. It calls reusable workflows,
each of which runs a mise task — so CI and local runs execute the same code.

| Job | Workflow | Runs |
|-----|----------|------|
| `lint` | `_lint.yml` | `SKIP=mise-lock mise run pre_commit_run_all` |
| `audit` | `_audit.yml` | `mise run audit` (`mode: pr` diffs against the base branch) |
| `test` | `_test.yml` | `mise run test:unit`, `test:integration`, `test:e2e`, `test:lowest_direct`, `test:python_versions`, then SonarQube |
| `publish_package` | `_package-publish.yml` | `uv build` + `uv publish`, tags `v*` only |

Everything else is independent: `lint-workflows.yml` (action pins), `bump.yml` (release
bump, triggered by `mise run bump`), and `test-scheduled-daily.yml` — one cron entry
point running `mise run test:all`, with an optional BetterStack heartbeat.

## MUST

- Reproduce a CI failure locally with the mise task from the table above before
  changing a workflow. The workflow is a thin wrapper; the bug is usually in the task.
- Pin every action to a full commit SHA with a `# vX.Y.Z` comment.
  `lint-workflows.yml` enforces this.
- Add new work as a mise task first, then call it from a workflow.

## MUST NOT

- Do not inline shell logic that belongs in a mise task — CI must stay reproducible locally.
- Do not add GCP/WIF auth or `id-token: write` to `lint`, `audit` or `test`. They need no
  credentials (public PyPI only). `publish_package` keeps `id-token: write` for PyPI
  trusted publishing.
- Do not re-enable the `mise-lock` pre-commit hook in CI. It mutates `mise.lock`, which
  CI cannot commit, so the job fails on a modified file.
- Do not treat a green PR as sufficient: the `protect_main` ruleset requires no status
  checks, so failures do not block a merge. Read the checks.

`[skip ci]` in a commit message skips the quality gates. SonarCloud gates the PR
separately from the workflows, on coverage of new code and rating regressions;
its exclusions live in `sonar-project.properties`. Secrets in use: `SONAR_TOKEN`, plus
optional `BETTERSTACK_HEARTBEAT_URL_DAILY` for the daily cron.
