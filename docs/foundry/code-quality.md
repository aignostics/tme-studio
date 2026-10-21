> [!NOTE]
> This file is maintained by the foundry-python template and will be updated when you run `mise run update_from_template`.

# Code Quality

## Linting & Type Checking

```shell
mise run lint   # Runs Ruff + Pyrefly
```

| Tool | Mode | Purpose |
|------|------|---------|
| Ruff | Format + Lint | Code style, 120 char limit, Google-style docstrings |
| Pyrefly | Type checking | Fast Rust-based type checker |

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

Contents are production-only (`uv export --no-dev`): your test and lint tools are
not part of what you ship, and an SBOM that lists them is one an auditor has to
argue with. `reports/audit-all.json` covers dev dependencies for vulnerabilities.

To see the difference on a real, two-dependency project, read
[`sbom-before.json`](https://github.com/aignostics/foundry-python/blob/main/tests/fixtures/sbom-before.json)
and [`sbom-after.json`](https://github.com/aignostics/foundry-python/blob/main/tests/fixtures/sbom-after.json)
in the template repository. They are unedited trivy output, and the test suite
regenerates the second from the first, so they cannot go stale.

---

## Pre-commit Hooks

### Automatic Hooks (pre-commit stage)

| Hook | Purpose |
|------|---------|
| ruff | Format and lint code |
| pyrefly | Type checking |
| detect-secrets | Scan for exposed credentials |
| uv-lock | Keep uv.lock synchronized |
| check-toml, check-xml | Validate config file syntax |
| debug-statements | Find leftover debugger calls (pdb, breakpoint) |
| end-of-file-fixer | Ensure files end with newline |
| trailing-whitespace | Remove trailing whitespace |

### Pre-push Hooks

| Hook | Purpose |
|------|---------|
| test-unit | Run unit tests before push |

### Commit Message Validation

Uses Commitizen to enforce [conventional commits](https://www.conventionalcommits.org/):

```
type(scope): description

# Examples:
feat(api): add user authentication
fix(parser): handle edge case in date parsing
docs(readme): update installation instructions
chore(deps): update dependencies
```

### Manual Hook Execution

```shell
mise run pre_commit_run_all   # Run all hooks on entire codebase
```

---

## Task Reference

### Setup & Installation

| Task | Description |
|------|-------------|
| `mise run install` | Sync all dependencies (`uv sync --all-extras`) + install pre-commit hooks |
| `mise run setup` | Post-generation environment setup |
| `mise run clean` | Remove all build artifacts and caches |

### Code Quality

| Task | Description |
|------|-------------|
| `mise run lint` | Run Ruff, Pyrefly |
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
| `mise run pre_commit_run_all` | Run all pre-commit hooks on all files |

### Passing Arguments to Tasks

Some tasks accept arguments. Use `--` to separate mise options from task arguments:

```shell
mise run <task> -- <arguments>
```

For example, to run an audit against a baseline file (only new findings fail):

```shell
mise run audit -- --baseline reports/audit.json
```
