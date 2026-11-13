> [!NOTE]
> Maintained by [foundry-python](https://github.com/aignostics/foundry-python) and updated by `mise run update_from_template`. Changed it? [Send it upstream](README.md#changed-a-template-file-send-it-upstream).

# Testing

## Test Markers

Every test needs a category marker (`unit`, `integration` or `e2e`). CI selects tests by marker, so `tests/conftest.py` fails the run with a usage error listing any test without one.

| Marker | Command | Purpose |
|--------|---------|---------|
| `@pytest.mark.unit` | `mise run test:unit` | Isolated tests, all dependencies mocked, must pass offline |
| `@pytest.mark.integration` | `mise run test:integration` | Real local services (Docker), mocked external APIs |
| `@pytest.mark.e2e` | `mise run test:e2e` | Real external services, full workflows |
| `@pytest.mark.scheduled` | `mise run test:scheduled` | Tests run on schedule (also included in regular runs) |
| `@pytest.mark.sequential` | `mise run test:sequential` | Tests excluded from parallel execution |

## Running Tests

```shell
# By category
mise run test:unit              # serial
mise run test:integration       # parallel, then `sequential` tests serially
mise run test:e2e               # parallel, then `sequential` tests serially

# All tests, then the coverage floor
mise run test

# Specific test
pytest tests/path/to/test.py::test_function -v
```

## Test Parallelization

Unit tests run serially: process start-up costs more than they take. Integration and e2e tests run with `-n auto`, one worker per CPU core times `XDIST_WORKER_FACTOR` (default `1`; e.g. `XDIST_WORKER_FACTOR=0.5 mise run test:e2e`). Tests marked `sequential` run afterwards without xdist.

## Coverage

- **Goal**: 100%
- **Minimum**: 85%, checked by `mise run test:coverage` over the combined runs (`mise run test` and CI run it last; CI skips it when a `skip:test:*` marker or label is set)
- **New code**: on pull requests CI waits for the SonarCloud quality gate and fails if it is red. Its conditions, such as coverage on new code, are configured in SonarCloud, not in the repository.
- **Reports**: `reports/coverage.xml`, `reports/coverage.md`, `reports/coverage_html/`

## Test Order Randomization

Tests run in randomized order via [`pytest-randomly`](https://github.com/pytest-dev/pytest-randomly) to surface hidden ordering dependencies between tests. To reproduce an order-dependent failure, rerun with the seed pytest printed: `pytest -p randomly --randomly-seed=<seed>`.

---

## Task Reference

| Task | Description |
|------|-------------|
| `mise run test` | unit → integration → e2e, then the coverage floor |
| `mise run test:unit` | Unit tests (serial) |
| `mise run test:integration` | Integration tests (parallel) |
| `mise run test:e2e` | E2E tests (parallel) |
| `mise run test:lowest_direct` | Fails on HIGH or CRITICAL vulnerabilities in the lowest allowed versions of direct dependencies, then runs unit tests against those versions |
| `mise run test:scheduled` | Scheduled tests only |
| `mise run test:sequential` | Non-parallelizable tests |
| `mise run test:coverage` | Fail if combined coverage is below 85% |
| `mise run test:coverage_reset` | Clear coverage data |

## Dependency Versions (libraries)

A library CI tests two dependency sets and publishes SBOMs for a third.
Locked is what CI tests and what services install.
Lowest-direct is the oldest set that a consumer can resolve inside the declared ranges.
Highest is what a new consumer without a lock gets on the release day, so only its SBOM is published.
`test:lowest_direct` exports the lowest-direct SBOM with `--no-build`, then Trivy fails on HIGH or CRITICAL findings, then uv syncs and the tests run.
Before the scan passes, no lowest-direct package archive downloads and no package build runs. The scan covers dev dependencies too.
It finds only known vulnerabilities. MEDIUM, LOW, and `.trivyignore` findings pass, and a new malicious release is not known yet.
The 5-day `exclude-newer` cooldown covers that case. A floor that has only a source distribution fails the gate.
If the gate fails, raise the floor in `pyproject.toml`. Or add a `.trivyignore` entry with the reason, the ticket, and the expiry date. See [exceptions](https://github.com/aignostics/alexandria-techorg/blob/main/tech/security/supply_chain/exceptions.md).
Details: [ADR-0002](https://github.com/aignostics/foundry-python/blob/main/docs/decisions/ADR-0002-test-libraries-against-three-dependency-sets.md).
