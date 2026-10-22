> [!NOTE]
> This file is maintained by the foundry-python template and will be updated when you run `mise run update_from_template`.

# Testing

## Test Markers

Every test **MUST** have a category marker. Tests without markers won't run in CI.

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
mise run test:unit              # Fast, isolated (serial execution)
mise run test:integration       # Real services (20% parallel)
mise run test:e2e               # Full parallel

# All tests
mise run test           # Runs unit → integration → e2e

# Specific test
pytest tests/path/to/test.py::test_function -v
```

## Test Parallelization

Controlled by `XDIST_WORKER_FACTOR` environment variable:

| Test Type | Factor | Behavior |
|-----------|--------|----------|
| Unit | 0.0 | Serial (parallelization overhead > benefit) |
| Integration | 0.2 | 20% of logical CPUs |
| E2E | 1.0 | 100% of logical CPUs (I/O bound) |

## Coverage

- **Goal**: 100%
- **Minimum**: 85%
- **Reports**: `reports/coverage.xml`, `reports/coverage.md`, `reports/coverage_html/`

## Test Order Randomization

Tests run in randomized order via [`pytest-randomly`](https://github.com/pytest-dev/pytest-randomly) to surface hidden ordering dependencies between tests.

## Finding Unmarked Tests

```shell
pytest --collect-only -m "not unit and not integration and not e2e" -q
```

---

## Task Reference

| Task | Description |
|------|-------------|
| `mise run test` | Run all tests (unit → integration → e2e) |
| `mise run test:unit` | Unit tests only (serial) |
| `mise run test:integration` | Integration tests (20% parallel) |
| `mise run test:e2e` | E2E tests (full parallel) |
| `mise run test:scheduled` | Scheduled tests only |
| `mise run test:sequential` | Non-parallelizable tests |
| `mise run test:coverage_reset` | Clear coverage data |
