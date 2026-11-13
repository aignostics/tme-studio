> [!NOTE]
> Maintained by [foundry-python](https://github.com/aignostics/foundry-python) and updated by `mise run update_from_template`. Changed it? [Send it upstream](README.md#changed-a-template-file-send-it-upstream).

# Getting Started: TME Studio

Everything needed to get this project fully operational, once, after scaffolding.

## Toolchain

This project was scaffolded using [foundry-python](https://github.com/aignostics/foundry-python):

| Category | Tools |
|----------|-------|
| **Tasks & tools** | [mise](https://mise.jdx.dev/) (tool versions, tasks), [uv](https://docs.astral.sh/uv/) (dependencies, build, publish) |
| **Code Quality** | [Ruff](https://github.com/astral-sh/ruff) (lint, format), [Pyrefly](https://github.com/facebook/pyrefly) (types), [deptry](https://github.com/fpgmaas/deptry) (dependency hygiene) |
| **Git Hooks** | [pre-commit](https://pre-commit.com/), [detect-secrets](https://github.com/Yelp/detect-secrets), [Commitizen](https://commitizen-tools.github.io/commitizen/) |
| **Testing** | [pytest](https://docs.pytest.org/) with xdist and randomized order, coverage floor, [SonarCloud](https://sonarcloud.io/) quality gate |
| **CI/CD** | [GitHub Actions](https://github.com/features/actions), [act](https://github.com/nektos/act) (run locally), actionlint and pinact (workflow lint) |
| **Security** | [trivy](https://trivy.dev/) (vulnerabilities, licenses, CycloneDX/SPDX SBOMs), Dependabot alerts, daily scheduled audit |
| **Dependencies** | [Renovate](https://github.com/renovatebot/renovate) (updates, 5-day minimum release age) |
| **AI Assistance** | `AGENTS.md` files, [Claude Code](https://docs.claude.com/en/docs/claude-code/github-actions) PR reviews (`claude` label) |

---

## Verify Installation

Before configuring services, confirm the local environment is working:

```shell
mise run install
```

Then run all git hooks on the fresh project:

```shell
# pre-commit stage (runs on every git commit: lint, secret detection, formatting)
mise run pre_commit_run_all

# pre-push stage (runs on git push: unit tests)
mise run pre_push_run_all
```

Both should pass. If the first run fixes files, stage them and run again; that is expected on a fresh checkout. Finally, `mise run test` should pass.

---

## Service Connections

| Service | Purpose | Status |
|---------|---------|--------|
| [GitHub Repository Settings](#github-repository-settings) | Security alerts, Dependabot | |
| [GitHub Branch Ruleset](#github-branch-ruleset) | `main` branch protection rules | |
| [Google Artifact Registry](#google-artifact-registry) | Package publishing | |
| [SonarCloud](#sonarcloud) | Code quality analysis | |
| [Renovate](#renovate) | Dependency updates | |
| [Repository Polish](#repository-polish) | Discoverability | |

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

> **Prerequisite**: the repository is pushed to GitHub, and `gh` is authenticated (`mise` installs it).

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

Locally, `gcloud auth login --update-adc` is all it takes: mise hands gcloud's token to uv (`.mise/scripts/registry_token.sh`), and falls back to uv's keyring provider when gcloud has none. If `uv sync` answers 401 or "Missing credentials", that login has expired — run it again.

If this repo publishes packages to GAR (`uv publish`), it needs `python-gar-writer` access. Ask the Platform Engineering team in [#support-platform-engineering](https://aignostics.slack.com/archives/C08SYE0JV3M) to set the `python_gar_access` custom property to `python-gar-writer` on this repo. This is an org-admin operation and cannot be done via repository settings.

**Verify**: the `Setup Dev Environment` step succeeds in the lint, test or audit workflow.

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
| [SonarCloud](https://sonarcloud.io/project/overview?id=aignostics_tme-studio) | Code quality, security and coverage | `SONAR_TOKEN` is org-wide; a red quality gate fails the PR |
| [Sentry](https://sentry.io/) | Error monitoring | Org-level integration; scans PRs automatically |
| [Ox Security](https://app.ox.security/) | Supply chain security | Org-level integration; scans PRs automatically |
| [Dependabot](https://github.com/aignostics/tme-studio/settings/security_analysis) | Dependency vulnerability alerts | Enabled by default via enterprise policy |
| [Claude Code](https://github.com/aignostics/tme-studio/actions) | AI-powered PR reviews (`claude` label) | Workload identity federation via org-level `ANTHROPIC_*` variables; no setup required |

### Renovate

**Why**: automated, grouped dependency updates. Dependabot keeps handling security alerts.

1. Go to https://developer.mend.io and sign in with your GitHub account
2. Go to https://developer.mend.io/github/aignostics/tme-studio and click **Action > Run Renovate scan**
3. Renovate creates a [Dependency Dashboard](https://github.com/aignostics/tme-studio/issues?q=is%3Aissue%20state%3Aopen%20Dependency%20Dashboard) issue in your repository

**Verify**: Dependency Dashboard issue appears in your repository

### Repository Polish

1. Go to https://github.com/aignostics/tme-studio
2. Click the cogs icon next to "About"
3. Copy the description from `pyproject.toml` into the description field
4. Copy up to 20 tags from `pyproject.toml` into the topics field
5. Go to https://github.com/aignostics/tme-studio/settings and upload a social preview image (e.g. `logo.png`)


---

Next: the rest of [docs/foundry](README.md).
