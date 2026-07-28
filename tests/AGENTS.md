# AGENTS.md — tests

Root guidance: [../AGENTS.md](../AGENTS.md)

## Running

```bash
mise run test:unit            # solitary, offline, all dependencies mocked
mise run test:integration     # sociable: real file I/O and subprocesses, external services mocked
mise run test:e2e             # real external services, needs .env
mise run test                 # the three above
mise run test:lowest_direct   # unit tests against lowest-direct dependency resolution
mise run test:python_versions # unit tests on oldest + newest Python, via tox (`uv run tox -e py311`)
mise run test:coverage_reset  # drop accumulated coverage data
```

Marker definitions, pytest options, the 10s default timeout and coverage settings are
in `pyproject.toml`. Task-level flags (xdist, junit output, `--cov-append`) are in
`tasks.toml`. Shared fixtures and hooks are in `tests/conftest.py`.

## MUST

- Mark every test `unit`, `integration` or `e2e`. Unmarked tests are collected by no
  task, so they never run and rot unnoticed.
- Name test files `<module>_test.py`, mirroring the `src/` layout. The
  `name-tests-test` pre-commit hook enforces it.
- Add `sequential` to any test that cannot tolerate parallel execution. The
  integration and e2e tasks run `not sequential` under xdist first, then `sequential`
  on its own.
- Keep a test under the 10s default timeout. Override deliberately with
  `@pytest.mark.timeout(N)` rather than raising the default.
- Extract repeated string literals into module-level constants — tests are held to the
  same SonarQube rules as `src/`.

## MUST NOT

- Do not call external services from `unit` or `integration` tests; they must pass
  offline.
- Do not share state between tests, and do not order-couple them.
- Do not use `sleep` or wall-clock timing to synchronise.
- Do not mock internal logic. Mock at the boundary you are isolating.
