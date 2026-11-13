> [!NOTE]
> Maintained by [foundry-python](https://github.com/aignostics/foundry-python) and updated by `mise run update_from_template`. Changed it? [Send it upstream](README.md#changed-a-template-file-send-it-upstream).

# Code Quality

## Linting & Type Checking

```shell
mise run lint     # check
mise run format   # fix what Ruff can
```

| Tool | Purpose |
|------|---------|
| Ruff | Lint (all rules, preview) and format: 120 chars, Google-style docstrings |
| Pyrefly | Type checking |
| deptry | Undeclared, unused or misplaced dependencies |

## Security & Compliance

```shell
mise run audit   # Runs all security checks
```

| Tool | Purpose | Output |
|------|---------|--------|
| trivy | Vulnerability and license scan, production dependencies | `reports/audit-prod.json` |
| trivy | Vulnerability scan, including dev dependencies | `reports/audit-all.json` |
| trivy | CycloneDX SBOM, production dependencies | `reports/sbom.json` |
| trivy | SPDX SBOM, production dependencies | `reports/sbom.spdx` |

### Reading the findings

Vulnerabilities are listed in Trivy's table format, with their severity, fixed
version and title:

```
=== Production: Vulnerability Check (fails on CRITICAL, HIGH) ===
Vulnerabilities found:

requirements.txt (pip)
======================
Total: 2 (UNKNOWN: 0, LOW: 0, MEDIUM: 1, HIGH: 1, CRITICAL: 0)

┌──────────┬────────────────┬──────────┬────────┬───────────────────┬────────────────┬─────────────────────────────────────────────────────────────┐
│ Library  │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version  │                            Title                            │
├──────────┼────────────────┼──────────┼────────┼───────────────────┼────────────────┼─────────────────────────────────────────────────────────────┤
│ requests │ CVE-2024-35195 │ MEDIUM   │ fixed  │ 2.25.0            │ 2.32.0         │ requests: subsequent requests to the same host ignore cert  │
│          │                │          │        │                   │                │ verification                                                │
│          │                │          │        │                   │                │ https://avd.aquasec.com/nvd/cve-2024-35195                  │
├──────────┼────────────────┼──────────┤        ├───────────────────┼────────────────┼─────────────────────────────────────────────────────────────┤
│ urllib3  │ CVE-2023-43804 │ HIGH     │        │ 1.26.4            │ 2.0.6, 1.26.17 │ python-urllib3: Cookie request header isn't stripped during │
│          │                │          │        │                   │                │ cross-origin redirects                                      │
│          │                │          │        │                   │                │ https://avd.aquasec.com/nvd/cve-2023-43804                  │
└──────────┴────────────────┴──────────┴────────┴───────────────────┴────────────────┴─────────────────────────────────────────────────────────────┘

1 finding(s) at CRITICAL, HIGH fail the audit. Upgrade each package to its fixed version, or accept a finding by adding its ID to .trivyignore with a comment saying why.
```

In pull-request mode (`--baseline`), findings the PR introduces and findings that
were already there are shown in separate tables.

By default, HIGH and CRITICAL vulnerabilities fail the audit. Lower severities are
listed but do not fail it. To choose the severities that fail, pass a
comma-separated list:

```shell
mise run audit --severity CRITICAL
mise run audit --severity MEDIUM,HIGH,CRITICAL
```

Upgrade the package to its fixed version where there is one. To accept a finding
instead, add its ID to `.trivyignore` with a comment saying why it does not apply,
and optionally an expiry (`exp:YYYY-MM-DD`) so it gets reviewed again.

### What the SBOMs say

Both SBOMs describe **this project**, under the name and version in
`pyproject.toml`:

```json
"component": { "type": "application", "name": "acme-example-project", "version": "1.2.3" }
```

Trivy names an SBOM after whatever it scanned and has no flag to change it, so
`run_audit.sh` renames the scan before converting it. Left alone, both SBOMs
describe a thing called `requirements.txt` with no version, and anything that reads
the root component as a package — Ketryx, Dependency-Track, GitHub's dependency
graph — lists the scan target as if it were one of your dependencies.

The root component carries no purl. `pkg:pypi/...` would claim these releases go to
PyPI; they go to `aignx-private-registry`. A name and a version are all CycloneDX
asks of a root component.

Dependencies **from that registry** say so, using the purl `repository_url`
qualifier and the registry `uv.lock` records for each one:

```
pkg:pypi/certifi@2024.2.2
pkg:pypi/aignx-cora-client@1.5.0?repository_url=https://europe-python.pkg.dev/…/simple/
```

Packages that genuinely come from PyPI are left bare on purpose — qualifying them
would stop their purls matching public vulnerability databases, which is what purls
are for.

The qualifier is what pins one of our packages to the registry it actually came
from, so nothing downstream can resolve it against public PyPI and match a
different package of the same name.

Contents are production-only (`uv export --no-default-groups`): your test and lint tools are
not part of what you ship, and an SBOM that lists them is one an auditor has to
argue with. `reports/audit-all.json` covers dev dependencies for vulnerabilities.

To see the difference on a real, two-dependency project, read
[`sbom-before.json`](https://github.com/aignostics/foundry-python/blob/main/tests/fixtures/sbom-before.json)
and [`sbom-after.json`](https://github.com/aignostics/foundry-python/blob/main/tests/fixtures/sbom-after.json)
in the template repository. They are unedited trivy output, and the test suite
regenerates the second from the first, so they cannot go stale.

Releases also carry `sbom-lowest-direct.json` and `sbom-highest.json`, which uv writes.
The root-component and purl rules above apply to `sbom.json` only.
uv names the root component after the project and adds the `repository_url` qualifier to non-PyPI packages.

### Security floors

`[tool.uv]` in `pyproject.toml` sets minimum versions that a relock cannot undo.
`override-dependencies` holds a floor for each transitive package with a known
vulnerability, and each entry names the advisory. `required-version` holds the
lowest uv that you can use, because uv ships its own CA certificates.

The current floors for `certifi`, `pip` and uv remove the eMudhra/emSign CAs from
the trust store. For details, read the
[Python advisory](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).
If you remove a floor, a later `uv lock` can bring back the vulnerable version.

### Dependency cooldown

`exclude-newer = "5 days"` in `[tool.uv]` stops `uv lock` from picking a PyPI release
that is less than 5 days old. Renovate holds direct dependency updates for the same
5 days through `minimumReleaseAge`. Renovate cannot hold lock file maintenance,
because a lock file refresh has no release timestamp. The uv setting closes that gap
for transitive dependencies. `aignx-private-registry` is exempt
(`exclude-newer = false`), because it publishes no upload times.

To ship a security fix before its 5 days pass:

1. Under `[tool.uv.exclude-newer-package]`, add `<package> = "<publish date + 1 day>T00:00:00Z"`.
   Above it, add a comment that names the fix and the removal date (publish date + 5 days).
2. Run `uv lock --upgrade-package <package>`.
3. Remove the entry on or after the removal date.

If you keep an entry after its removal date, it blocks all later releases of the
package, and Renovate's lock update for that package fails.

---

## Git Hooks

Installed by `mise run install`. Hooks stop at the first failure (`fail_fast`).

| Stage | Hook | Purpose |
|-------|------|---------|
| commit | `lint` | `mise run lint` |
| commit | `uv-lock`, `mise-lock` | Re-lock and stage `uv.lock` / `mise.lock` when their config changes |
| commit | `detect-secrets` | Block credentials, against `.secrets.baseline` |
| commit | [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks), [pygrep-hooks](https://github.com/pre-commit/pygrep-hooks) | File hygiene: large files, merge markers, private keys, TOML/XML syntax, debugger calls, whitespace, `*_test.py` naming |
| commit-msg | `commitizen` | [Conventional commit](https://www.conventionalcommits.org/) message: `type(scope): description` |
| push | `test-unit` | `mise run test:unit --no-cov -x`: no coverage, stop at the first failure |

Run them on all files: `mise run pre_commit_run_all`, `mise run pre_push_run_all`.

---

## Task Reference

### Setup & Installation

| Task | Description |
|------|-------------|
| `mise run install` | Sync all dependencies (`uv sync --all-extras`) + install pre-commit hooks |
| `mise run setup` | Post-generation setup (runs once, from copier) |
| `mise run update_from_template` | Merge the latest foundry-python release, then lint and audit |
| `mise run clean` | Remove all build artifacts and caches |

### Code Quality

| Task | Description |
|------|-------------|
| `mise run lint` | Ruff, Pyrefly, deptry |
| `mise run format` | Ruff fixes and formatting |
| `mise run audit` | Security scanning + SBOM generation |
| `mise run attributions` | Generate `reports/ATTRIBUTIONS.md` (also uploaded as CI artifact) |



### Attribution Generation

`mise run attributions` generates `reports/ATTRIBUTIONS.md` — a list of all third-party open source packages used by this project, with their licenses. This file is not committed to the repository; it is generated in CI as part of the audit and uploaded as a build artifact.

To generate it locally:

```shell
mise run attributions
# Output: reports/ATTRIBUTIONS.md
```

### Utilities

| Task | Description |
|------|-------------|
| `mise run all` | Full validation: lint + test + attributions + audit |
| `mise run act` | Run GitHub Actions locally with act |
| `mise run pre_commit_run_all` / `pre_push_run_all` | Run the git hooks on all files |

### Passing Arguments to Tasks

Use `--` to separate mise options from task arguments. For example, fail only on findings that are not in a baseline:

```shell
mise run audit -- --baseline reports/audit-prod.json
```
