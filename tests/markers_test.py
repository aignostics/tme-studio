"""Placeholder test per marker.

Keeps every marker non-empty so a marker-filtered run (`mise run test:scheduled`,
`test:sequential`, ...) always collects at least one test instead of reporting an
empty selection.
"""

import pytest


@pytest.mark.unit
def test_unit_marker_selects_at_least_one_test() -> None:
    """Placeholder for the `unit` marker."""


@pytest.mark.integration
def test_integration_marker_selects_at_least_one_test() -> None:
    """Placeholder for the `integration` marker."""


@pytest.mark.e2e
def test_e2e_marker_selects_at_least_one_test() -> None:
    """Placeholder for the `e2e` marker."""


@pytest.mark.scheduled
@pytest.mark.unit
def test_scheduled_marker_selects_at_least_one_test() -> None:
    """Placeholder for the `scheduled` marker.

    Also carries `unit` because every test needs a category marker to run in CI.
    """


@pytest.mark.sequential
@pytest.mark.unit
def test_sequential_marker_selects_at_least_one_test() -> None:
    """Placeholder for the `sequential` marker.

    Also carries `unit` because every test needs a category marker to run in CI.
    """
