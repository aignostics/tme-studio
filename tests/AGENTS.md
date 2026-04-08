# AGENTS.md - Test Suite

This file provides guidance for working with the test suite. For general project guidance, see the root [AGENTS.md](../AGENTS.md).

## Critical Test Patterns

### Test Markers

**CRITICAL**: Every test **MUST** have at least one of: `unit`, `integration`, or `e2e`. Tests without these markers won't run in CI.

```python
# CORRECT - Has category marker
@pytest.mark.unit
def test_something():
    pass


# INCORRECT - No category marker, will NOT run in CI
def test_something_else():
    pass


# CORRECT - Multiple markers including category
@pytest.mark.e2e
@pytest.mark.sequential
def test_complex_workflow():
    pass
```

### Available Markers

From `pyproject.toml`:

```python
scheduled = "Tests to run on a schedule"
sequential = "Tests that must run in specific order"
unit = "Solitary unit tests (no external services)"
integration = "Sociable integration tests (real local services)"
e2e = "End-to-end tests (real external services)"
```

## Test Categories

### 1. Unit Tests

**Marker**: `@pytest.mark.unit`

**Characteristics**:

- Fast, isolated tests with all dependencies mocked
- No external service calls (database, APIs, etc.)
- Timeout: ≤ 10s (default)

**Example**:

```python
@pytest.mark.unit
@patch("aignostics_tme_studio.module.ExternalClient")
def test_service_initialization(mock_client):
    """Test that Service initializes correctly."""
    service = Service()
    assert service is not None
    mock_client.assert_called_once()
```

**Run locally**:

```bash
mise run test_unit
# Or: pytest -m "unit" -v
```

### 2. Integration Tests

**Marker**: `@pytest.mark.integration`

**Characteristics**:

- Tests with real local services (e.g., database via Docker)
- Mocked external services (third-party APIs)
- Real file I/O, real subprocesses
- Timeout: ≤ 10s (default)

**Example**:

```python
@pytest.mark.integration
def test_database_persistence(db_session):
    """Test database persistence with real session."""
    record = MyModel(name="test")
    db_session.add(record)
    db_session.commit()

    saved = db_session.get(MyModel, record.id)
    assert saved is not None
```

**Run locally**:

```bash
mise run test_integration
# Or: pytest -m "integration" -v
```

### 3. E2E Tests

**Marker**: `@pytest.mark.e2e`

**Characteristics**:

- Complete workflows with real external services
- Requires credentials/configuration in `.env`
- Timeout: ≤ 10s (default)

**Run locally**:

```bash
mise run test_e2e
# Or: pytest -m "e2e" -v
```

### 4. Sequential Tests

**Marker**: `@pytest.mark.sequential`

**Characteristics**:

- Tests that must run in specific order
- Have interdependencies or shared state
- Cannot be parallelized

**Run locally**:

```bash
mise run test_sequential
# Or: pytest -m sequential -v
```

## Global Fixtures (conftest.py)

### Test Parallelization

**Dynamic worker calculation**:

```python
def pytest_xdist_auto_num_workers(config) -> int:
    """Calculate workers based on CPU count * XDIST_WORKER_FACTOR."""
    logical_cpu_count = psutil.cpu_count(logical=True) or 1
    factor = float(os.getenv("XDIST_WORKER_FACTOR", "1"))
    return max(1, int(logical_cpu_count * factor))
```

**Worker factors** (from `mise.toml`):

- `unit`: `0.0` (sequential, 1 worker)
- `integration`: `0.2` (20% of CPUs)
- `e2e`: `1.0` (100% of CPUs)

### Custom Exit Status

```python
def pytest_sessionfinish(session, exitstatus) -> None:
    """Change exit status 5 (no tests collected) to 0."""
    if exitstatus == 5:
        session.exitstatus = 0
```

**Why**: Prevents CI failures when running with specific markers and no tests match.

## Running Tests

### Quick Commands

```bash
# All default tests (unit + integration + e2e)
mise run test

# By category
mise run test_unit              # Unit tests only
mise run test_integration       # Integration tests only
mise run test_e2e               # E2E tests (may require .env)

# Special categories
mise run test_scheduled         # Scheduled tests only
mise run test_sequential        # Sequential tests only

# Coverage reset
mise run test_coverage_reset
```

### Direct Pytest Commands

```bash
# Run specific test file
pytest tests/aignostics_tme_studio/module_test.py -v

# Run specific test function
pytest tests/aignostics_tme_studio/module_test.py::test_function -v

# Run with markers
pytest -m "unit" -v
pytest -m "integration or e2e" -v

# Run with coverage
pytest --cov=src/aignostics_tme_studio --cov-report=term-missing

# Debug mode (drop into pdb on failure)
pytest tests/test_file.py --pdb

# Show print statements
pytest tests/test_file.py -s

# Verbose output
pytest tests/test_file.py -vv

# Parallel execution
pytest -n auto  # Uses all CPUs
pytest -n logical  # Uses logical CPUs
pytest -n 4  # Fixed 4 workers
```

## Test Parallelization

### Worker Configuration

From `noxfile.py` and `mise.toml`:

```python
XDIST_WORKER_FACTOR = {
    "unit": 0.0,  # No parallelization (fast enough)
    "integration": 0.2,  # 20% of logical CPUs
    "e2e": 1.0,  # 100% of logical CPUs (I/O bound)
    "default": 1.0,
}
```

**Example** (8 CPU machine):

- unit: `1 worker` (sequential)
- integration: `max(1, int(8 * 0.2))` = `1 worker`
- e2e: `max(1, int(8 * 1.0))` = `8 workers`

### Why Different Factors?

- **Unit tests (0.0)**: Fast enough that parallelization overhead hurts
- **Integration (0.2)**: Some I/O but mostly CPU-bound
- **E2E (1.0)**: Network I/O bound, full parallelization maximizes throughput

## Coverage Requirements

**Minimum Coverage**: 85% (goal: 100%)

```bash
# Check coverage
coverage report

# Generate HTML report
coverage html
open htmlcov/index.html

# Coverage enforced in CI
coverage report --fail-under=85
```

**Coverage Configuration** (from `pyproject.toml`):

```toml
[tool.coverage.run]
source = ["src/aignostics_tme_studio"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 85
```

## Debugging Test Failures

### Verbose Output

```bash
# Maximum verbosity
pytest -vvv --tb=long

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Test Isolation

```bash
# Run specific test
pytest tests/aignostics_tme_studio/module_test.py::test_function -v

# Run tests matching pattern
pytest -k "health" -v
```

### Debug Mode

```python
# Enable breakpoint in test
def test_complex_logic():
    result = complex_function()
    import pdb

    pdb.set_trace()  # Breakpoint
    assert result.status == "success"
```

**Or use pytest's `--pdb`**:

```bash
pytest tests/test_file.py --pdb
```

## Common Issues & Solutions

### Tests Not Running in CI

**Problem**: Tests exist but don't run in CI

**Cause**: Missing category marker (`unit`, `integration`, or `e2e`)

**Solution**: Add marker to test

### Import Errors

**Problem**: `ImportError` for project modules

**Solution**:

```bash
uv sync --all-extras
pytest  # Uses correct Python path
```

### Parallel Test Failures

**Problem**: Tests fail when run in parallel but pass sequentially

**Cause**: Shared state or race conditions

**Solution**: Mark test as `@pytest.mark.sequential`

### Coverage Drops

**Problem**: Coverage below threshold

**Solution**:

1. Check which files lack coverage: `coverage report -m`
2. Add tests for uncovered lines
3. Ensure tests are marked correctly (run in CI)

## Test Maintenance

### Adding New Tests

1. **Choose test file** based on module structure:
   - `tests/aignostics_tme_studio/<module>_test.py` for module tests

2. **Add appropriate markers**:

   ```python
   @pytest.mark.unit  # Or integration, e2e
   def test_new_feature():
       pass
   ```

3. **Use existing fixtures** from `conftest.py`

4. **Follow naming convention**: `test_<what>_<expected_behavior>`

### Updating Fixtures

**Global fixtures**: Edit `tests/conftest.py`

**Module fixtures**: Add to test file or module-specific `conftest.py`

### Verifying Test Discovery

```bash
# Collect tests without running
pytest --collect-only

# Find tests without category markers (won't run in CI)
pytest -m "not unit and not integration and not e2e" --collect-only
```

## Best Practices

1. **Always add category marker** (`unit`, `integration`, or `e2e`)
2. **Isolate tests** - No shared state between tests
3. **Use mocks for external services** in unit and integration tests
4. **Test one thing** - Each test should verify one behavior
5. **Clear test names** - `test_<action>_<expected_result>`
6. **Arrange-Act-Assert** pattern:

   ```python
   def test_example():
       # Arrange - Setup
       service = Service()

       # Act - Execute
       result = service.method()

       # Assert - Verify
       assert result == expected
   ```

7. **Mock at boundaries** - Mock external dependencies, not internal logic
8. **Use fixtures** for common setup
9. **Clean up resources** - Use fixtures with cleanup or `finally` blocks
10. **Avoid flaky tests** - No sleeps, no timing dependencies

---

*This test suite follows production-grade testing practices.*
