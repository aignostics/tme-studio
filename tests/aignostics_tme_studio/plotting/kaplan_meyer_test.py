"""Test module for Kaplan Meyer plots."""

import numpy as np
import pytest
from lifelines import KaplanMeierFitter
from plotly import graph_objects as go

from aignostics_tme_studio.plotting.kaplan_meyer import KaplanMeyerPlotter


def create_dummy_fitter(seed: int = 42) -> KaplanMeierFitter:
    """Create KaplanMeierFitter from random series of durations and events."""
    rng = np.random.default_rng(seed=seed)
    n = 100
    durations = rng.uniform(0, 100, size=n)
    event = rng.choice([1, 0], size=n)
    return KaplanMeierFitter().fit(durations, event)


@pytest.fixture(name="dummy_kmf")
def fixture_dummy_kmf() -> KaplanMeierFitter:
    """Create a dummy KaplanMeyerFitter."""
    return create_dummy_fitter()


@pytest.mark.unit
def test_kaplan_meyer_plotter(dummy_kmf) -> None:
    """Test that the plotter renders HTML."""
    plotter = KaplanMeyerPlotter(show_censors=True)

    fig = plotter.render(kmfs=[dummy_kmf])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4  # graph, upper and lower CI limit, and censors

    plotter = KaplanMeyerPlotter(show_censors=False)
    fig = plotter.render(kmfs=[dummy_kmf])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3  # graph, upper and lower CI limit.


@pytest.mark.unit
def test_kaplan_meyer_plotter_multiple_estimators() -> None:
    """Test that the plotter renders curves for multiple estimators."""
    kmfs = [create_dummy_fitter(seed) for seed in [42, 13, 82]]

    plotter = KaplanMeyerPlotter(show_censors=False)

    fig = plotter.render(kmfs=kmfs)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 9  # 3 times a graph, upper and lower CI limit.
