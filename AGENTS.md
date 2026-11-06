# AGENTS.md

**TME Studio** — a toolkit to explore the Aignostics OpenTME dataset.

Scoped guidance: [tests/AGENTS.md](tests/AGENTS.md) · [.github/AGENTS.md](.github/AGENTS.md)

## Everything runs through mise

`mise tasks` lists every task. Definitions live in [tasks.toml](tasks.toml) and
[.mise/tasks/](.mise/tasks) — read the task rather than a description of it.

```bash
mise run install          # first-time setup: uv sync + pre-commit hooks
mise run lint             # ruff format check, ruff check, pyrefly, deptry
mise run test:unit        # also: test:integration, test:e2e, test (all three)
mise run test:python_versions  # oldest + newest supported Python, via tox
mise run audit            # trivy vulns + licenses, SBOM
mise run all              # everything, run before opening a PR
```

## MUST

- Run `mise run lint` before running tests, and again before declaring work complete.
- Give every test a `unit`, `integration` or `e2e` marker. Unmarked tests never run.
- Extract a string literal into a module-level constant once it appears 3+ times,
  in tests too (SonarQube S1192).
- Use `uv add` / `uv remove` for dependencies, never hand-edit `dependencies`.
- Declare every package you import directly in `pyproject.toml`; deptry fails on
  imports satisfied only transitively.
- Write conventional commits (`feat:`, `fix:`, `chore:`, `ci:` …).

## MUST NOT

- Do not add a dependency for what the stdlib or an installed package already does.
- Do not restate tool configuration in prose. `pyproject.toml`,
  `.pre-commit-config.yaml`, `sonar-project.properties` and `.license-types-allowed`
  are the single source of truth.
- Do not commit generated files: `reports/**`, and the `requirements*.txt` that
  `mise run audit` writes.
- Do not "fix" marimo notebook idiom in `src/**/notebooks/**`. Cells are
  `def _(mo, df)` functions ending in a bare expression that renders their output, and
  `_`-prefixed names are cell-scoped. Ruff and Sonar exclusions cover them.
- Do not reformat or refactor code you were not asked to change.

Python is `>=3.11, <3.15`; CI tests the single version in `.python-version`.
