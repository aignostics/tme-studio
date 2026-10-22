> [!NOTE]
> This file is maintained by the [foundry-python](https://github.com/aignostics/foundry-python) template and will be updated when you run `mise run update_from_template`.

# Getting Started: TME Studio

This getting started guide covers everything needed to get this project fully operational.

## Toolchain

This project was scaffolded using [foundry-python](https://github.com/aignostics/foundry-python):

| Category | Tools |
|----------|-------|
| **Code Quality** | [Ruff](https://github.com/astral-sh/ruff) (linting), [Pyrefly](https://github.com/facebook/pyrefly) (type checking) |
| **Git Hooks** | [pre-commit](https://pre-commit.com/), [detect-secrets](https://github.com/Yelp/detect-secrets), [pygrep](https://github.com/pre-commit/pygrep-hooks), [Commitizen](https://commitizen-tools.github.io/commitizen/) |
| **Testing** | [pytest](https://docs.pytest.org/) (parallel execution), [mise](https://mise.jdx.dev/) (test orchestration), [SonarCloud](https://sonarcloud.io/) (coverage) |
| **CI/CD** | [GitHub Actions](https://github.com/features/actions) (workflows), [act](https://github.com/nektos/act) (local testing) |
| **Security** | [SonarQube](https://www.sonarsource.com/products/sonarcloud), [trivy](https://trivy.dev/) (vulns, licenses, SBOM), [Dependabot](https://docs.github.com/en/code-security/getting-started/dependabot-quickstart-guide) |
| **Dependencies** | [Renovate](https://github.com/renovatebot/renovate) (updates), [trivy](https://trivy.dev/) (license compliance) |
| **Observability** | [Sentry](https://sentry.io/) (errors, tracing, profiling), [BetterStack](https://betterstack.com/) (uptime monitoring) |
| **Documentation** | SBOM generation ([CycloneDX](https://cyclonedx.org/), [SPDX](https://spdx.dev/)), auto-generated attributions, dynamic badges |
| **AI Assistance** | [GitHub Copilot](https://docs.github.com/en/copilot) (custom instructions), [Claude Code](https://docs.claude.com/en/docs/claude-code/github-actions) (PR reviews) |

---

## Verify Installation

Before configuring services, confirm the local environment is working:

```shell
mise run install
```

Then run all git hooks to verify the freshly generated project is clean:

```shell
# pre-commit stage (runs on every git commit: lint, secret detection, formatting)
mise run pre_commit_run_all

# pre-push stage (runs on git push: unit tests)
mise run pre_push_run_all
```

Both should pass without changes. If the first run fixes files, stage them and run again — that is expected on a fresh checkout.

Finally, run the test suite:

```shell
mise run test
```

All tests should pass. If not, run `mise run install` first.

---

## Service Connections

| Service | Purpose | Status |
|---------|---------|--------|
| [GitHub Repository Settings](#github-repository-settings) | Security alerts, Dependabot | |
| [GitHub Branch Ruleset](#github-branch-ruleset) | `main` branch protection rules | |
| [Google Artifact Registry](#google-artifact-registry) | Package publishing | |
| [SonarCloud](#sonarcloud) | Code quality analysis | |
| [Renovate](#renovate) | Dependency updates | |
| [Sentry](#sentry--advanced-setup) | Error monitoring | |
| [Repository Polish](#repository-polish) | Discoverability | |
| [Background Worker](#background-worker) | Chancy job queue | |

---

## GitHub Repository Settings

**Why**: Ensures dependency vulnerability scanning is active.

1. Go to https://github.com/aignostics/tme-studio/settings/security_analysis
2. Verify **Dependabot alerts** is enabled (on by default via enterprise policy)
3. Verify **Dependabot security updates** is enabled (on by default via enterprise policy)
4. Do **NOT** enable Dependabot version updates — Renovate handles this
5. (Public repos only) Enable **Private vulnerability reporting**

### GitHub Branch Ruleset

**Why**: Protects `main` from force-pushes, direct deletions, and merges without reviewed PRs.

> **Prerequisite**: Push the repository to GitHub first (Quick Start step 4). Requires [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated.

A `.github-ruleset.json` file was generated in your project root when this project was scaffolded. Apply it once, then delete it:

```shell
gh api repos/aignostics/tme-studio/rulesets \
  --method POST \
  --header "Accept: application/vnd.github+json" \
  --input .github-ruleset.json

rm .github-ruleset.json
```

The file is git-ignored and will not be committed. Do not push it to the remote repository.

**Verify**: Go to https://github.com/aignostics/tme-studio/settings/rules — "main protection" should be listed.

---


### Google Artifact Registry

**Why**: This project's dependencies include private Python packages hosted in Aignostics' Google Artifact Registry (not on PyPI). CI workflows authenticate via org-level WIF variables — no per-repo secret is required.

Read access (`python-gar-reader`) is the org-wide default for all repos. No action needed for `uv sync` in CI.

If this repo publishes packages to GAR (`uv publish`), it needs `python-gar-writer` access. Ask the Platform Engineering team in [#support-platform-engineering](https://aignostics.slack.com/archives/C08SYE0JV3M) to set the `python_gar_access` custom property to `python-gar-writer` on this repo. This is an org-admin operation and cannot be done via repository settings.

**Verify**: the `Setup Dev Environment` step succeeds in lint, test or audit workflow

---

### SonarCloud

> **Note**: Requires SonarCloud admin access. Your team lead should have admin access; if not, ask in [#topic-foundry](https://aignostics.slack.com/archives/C0AEY02UQD6).

1. Go to https://sonarcloud.io/projects/create, select your new repo and click "Set Up"
    * **Do not** need to set a `SONAR_TOKEN` repository secret — the existing org-level token works for all repos
2. Select **Previous Code** when prompted
3. Go to https://sonarcloud.io/project/settings?id=aignostics_tme-studio → **Administration > Analysis Method** → disable **Automatic Analysis**
4. For private repositories — update the quality badge in `README.md`:
    * Go to https://sonarcloud.io/project/information?id=aignostics_tme-studio, scroll to **Badges**, copy the token from the URL, replace `SONAR_BADGE_TOKEN` in your `README.md`

---

## After Merging — Complete the Setup

The following do not block this PR. Complete them after merge to finish the project setup.

### Automated — No Action Required

These services are active automatically at the organisation level:

| Service | Purpose | Notes |
|---------|---------|-------|
| [SonarCloud](https://sonarcloud.io/project/overview?id=aignostics_tme-studio) | Code quality & security analysis & Coverage tracking | `SONAR_TOKEN` is org-wide; quality gate runs on every PR |
| [Sentry](https://sentry.io/) | Error monitoring | Org-level integration; scans PRs automatically |
| [Ox Security](https://app.ox.security/) | Supply chain security | Org-level integration; scans PRs automatically |
| [Dependabot](https://github.com/aignostics/tme-studio/settings/security_analysis) | Dependency vulnerability alerts | Enabled by default via enterprise policy |
| [Claude Code](https://github.com/aignostics/tme-studio/actions) | AI-powered PR reviews (`claude` label) | `ANTHROPIC_API_KEY` is org-wide; no setup required |

### Renovate

**Why**: Automated dependency updates with smart grouping and scheduling (complements Dependabot which handles security patches).

1. Go to https://developer.mend.io and sign in with your GitHub account
2. Go to https://developer.mend.io/github/aignostics/tme-studio and click **Action > Run Renovate scan**
3. Renovate creates a [Dependency Dashboard](https://github.com/aignostics/tme-studio/issues?q=is%3Aissue%20state%3Aopen%20Dependency%20Dashboard) issue in your repository

**Verify**: Dependency Dashboard issue appears in your repository

### Sentry — Advanced Setup

For error tracking, performance profiling, and release tracking, configure the Sentry DSN in your application code. Basic PR scanning is already active at the org level.

### Repository Polish

1. Go to https://github.com/aignostics/tme-studio
2. Click the cogs icon next to "About"
3. Copy the description from `pyproject.toml` into the description field
4. Copy up to 20 tags from `pyproject.toml` into the topics field
5. Go to https://github.com/aignostics/tme-studio/settings and upload a social preview image (e.g. `logo.png`)


---

## Background Worker

This project includes a [Chancy](https://chancy.readthedocs.io/) background worker powered by PostgreSQL.

### What was scaffolded

- `src/tme_studio/scheduler/` — the scheduler module (service, CLI, API, settings)
- `src/tme_studio/hello_world/_jobs.py` and `src/tme_studio/system/_jobs.py` — example job definitions
- `migrations/versions/0002_add_scheduler_heartbeats.py` — database migration for the heartbeat table
- `deployment/cloudrun/service-worker.template.yaml` — Cloud Run worker service definition

### Run the worker locally

Start everything with Docker Compose (the worker service starts alongside the API and PostgreSQL):

```shell
docker compose up
```

Or run the worker directly:

```shell
# Apply the scheduler database migration first
uv run tme-studio scheduler db migrate

# Register job definitions
uv run tme-studio scheduler joblets register

# Start the worker
uv run tme-studio scheduler execute
```

The Chancy web UI is available at `http://127.0.0.1:8001` by default (configurable via `TME_STUDIO_SCHEDULER_API_HOST` and `TME_STUDIO_SCHEDULER_API_PORT`).

### Database migration

The scheduler requires its own migration to create the heartbeat table. This runs automatically at startup in production (see `deployment/cloudrun/service.template.yaml`). Locally, run:

```shell
uv run tme-studio scheduler db migrate
```

### Chancy metrics

The worker does not load the Chancy Metrics plugin. It loads the metric rows of all workers into memory, and the table grows with each worker restart. Use OpenTelemetry for metrics (see [opentelemetry.md](opentelemetry.md)). The Chancy web UI has no Metrics page.

Chancy adds Metrics as a default plugin. Keep `no_default_plugins=True` and `Leadership()` in `scheduler/_service.py`.

**Upgrade path:** run `mise run update_from_template` and deploy. To remove the old table, add an Alembic migration to your project. Run it only after every instance runs the new code:

```sql
DROP TABLE IF EXISTS chancy_<name>_metrics;
DELETE FROM chancy_<name>_schema_version WHERE version_of = 'metrics';
```

On a new database, the version table does not exist yet. Guard the `DELETE` with `to_regclass('chancy_<name>_schema_version') IS NOT NULL`.

---

## Further Reading

- [docs/foundry/testing.md](testing.md) - Test markers, running tests, coverage
- [docs/foundry/ci-cd.md](ci-cd.md) - CI/CD workflows, releases, versioning
- [docs/foundry/code-quality.md](code-quality.md) - Linting, pre-commit hooks, task reference
- [docs/foundry/troubleshooting.md](troubleshooting.md) - Common issues and solutions
