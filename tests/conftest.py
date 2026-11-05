"""Common test fixtures and configuration."""

import logging
import os
import re

import psutil
import pytest

logger = logging.getLogger(__name__)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mGKH]")
_CATEGORY_MARKERS = frozenset({"unit", "integration", "e2e"})


def normalize_output(s: str, *, strip_line_endings: bool = True) -> str:
    """Strip ANSI escape codes from CLI output."""
    result = _ANSI_ESCAPE.sub("", s)
    if strip_line_endings:
        result = result.strip()
    return result


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Fail on tests without a category marker: CI selects by marker, so they would never run.

    Runs before `-m` deselects them. Skipped on xdist workers, where the error is unreadable; the
    serial unit run collects the whole suite anyway.

    Raises:
        pytest.UsageError: If any collected test lacks a category marker.
    """
    if hasattr(config, "workerinput"):
        return
    unmarked = [item.nodeid for item in items if not _CATEGORY_MARKERS & {m.name for m in item.iter_markers()}]
    if unmarked:
        listing = "\n  ".join(unmarked)
        msg = f"Tests without a category marker (unit, integration or e2e) would never run in CI:\n  {listing}"
        raise pytest.UsageError(msg)


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    """Set the number of workers for xdist to a factor of the (logical) CPU cores.

    If the pytest option `--numprocesses` is set to "logical" or "auto", the number of workers is calculated
    based on the logical CPU count multiplied by the factor. If the option is set otherwise, that value is
    used directly.

    The factor (float) can be adjusted via the environment variable `XDIST_WORKER_FACTOR`, defaulting to 1.

    Args:
        config: The pytest configuration object.

    Returns:
        int: The number of workers set for xdist.
    """
    if config.getoption("numprocesses") in {"logical", "auto"}:
        logical_cpu_count = psutil.cpu_count(logical=config.getoption("numprocesses") == "logical") or 1
        factor = float(os.getenv("XDIST_WORKER_FACTOR", "1"))
        print(f"xdist_worker_factor: {factor}")
        num_workers = max(1, int(logical_cpu_count * factor))
        print(f"xdist_num_workers: {num_workers}")
        logger.info(
            "Set number of xdist workers to '%s' based on logical CPU count of %s.", num_workers, logical_cpu_count
        )
        return num_workers
    result = config.getoption("numprocesses")
    return int(result) if result is not None else 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Run after the test session ends.

    Does change behavior if no test matching the marker is found:
    - Sets the exit status to 0 instead of 5.

    Args:
        session: The pytest session object.
        exitstatus: The exit status of the test session.
    """
    if exitstatus == 5:
        session.exitstatus = 0
