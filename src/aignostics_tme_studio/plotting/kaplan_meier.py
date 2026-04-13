"""Predefined plots."""

from collections.abc import Iterable
from textwrap import wrap

import numpy as np
import plotly.graph_objects as go
from lifelines import KaplanMeierFitter

from aignostics_tme_studio.styling.styling_utils import aignx_colors
from aignostics_tme_studio.utils import utils


def _plot_curves(fig: go.Figure, kmf: KaplanMeierFitter, rgb: tuple[int, ...]) -> go.Figure:
    """Plot the survival probability curve and its 95% confidence interval band.

    Args:
        fig: Plotly figure to add traces to.
        kmf: Fitted KaplanMeierFitter instance.
        rgb: RGB color tuple for the curve and CI band.

    Returns:
        The figure with the survival curve and CI band traces added.
    """
    r, g, b = rgb

    label = kmf.label
    # plot the probability curve
    fig.add_trace(
        go.Scatter(
            x=list(kmf.survival_function_.index),
            y=kmf.survival_function_[label],
            line={"shape": "hv", "width": 3, "color": f"rgba({r}, {g}, {b}, 1.)"},
            name="<br>".join(wrap(str(label), 20)),
        )
    )

    # plot upper CI limit
    fig.add_trace(
        go.Scatter(
            x=list(kmf.confidence_interval_.index),
            y=kmf.confidence_interval_[f"{label}_upper_0.95"],
            line={"shape": "hv", "width": 0},
            showlegend=False,
        )
    )

    # fill from upper to lower CI limit
    fig.add_trace(
        go.Scatter(
            x=list(kmf.confidence_interval_.index),
            y=kmf.confidence_interval_[f"{label}_lower_0.95"],
            line={"shape": "hv", "width": 0},
            fill="tonexty",
            showlegend=False,
            fillcolor=f"rgba({r}, {g}, {b}, 0.4)",
        )
    )
    return fig


def _plot_censures(fig: go.Figure, kmf: KaplanMeierFitter, censures: np.ndarray, rgb: tuple[int, ...]) -> go.Figure:
    """Plot censored observations as tick marks on the survival curve.

    Args:
        fig: Plotly figure to add traces to.
        kmf: Fitted KaplanMeierFitter instance.
        censures: Array of time points where censoring occurred.
        rgb: RGB color tuple for the censure markers.

    Returns:
        The figure with censure marker traces added.
    """
    r, g, b = rgb

    fig.add_trace(
        go.Scatter(
            x=censures,
            y=kmf.survival_function_at_times(censures),
            mode="markers",
            marker={"size": 8, "symbol": "line-ns", "line": {"width": 2, "color": f"rgba({r}, {g}, {b}, 1.)"}},
            showlegend=False,
        )
    )
    return fig


class KaplanMeierPlotter:
    """Plot a Kaplan Meier curves using interactive marimo UI elements."""

    def __init__(self, show_censors: bool = False) -> None:
        """Initialize `KaplanMeierPlotter`.

        Args:
            show_censors: If true, plot censure events as vertical lines on the curve.
        """
        self.show_censors = show_censors

    def render(self, kmfs: Iterable[KaplanMeierFitter], color_map: dict[str, str] | None = None) -> go.Figure:
        """Render the Kaplan Meier plots.

        Args:
            kmfs: List of KaplanMeierFitters to plot curves for.
            color_map: If given, use colors given under kmf label in this dictionary.

        Returns:
            The figure with plotted Kaplan Meier curves as a marimo UI object.
        """
        fig = go.Figure()

        for i, kmf in enumerate(kmfs):
            if not color_map or not color_map.get(kmf.label):
                color = aignx_colors[i % len(aignx_colors)]
            else:
                color = color_map.get(kmf.label)

            rgb = utils.hex_to_rgb(color)

            fig = _plot_curves(fig, kmf, rgb)

            if self.show_censors:
                censures = np.asarray(kmf.durations[~np.asarray(kmf.event_observed).astype(bool)])
                fig = _plot_censures(fig, kmf, censures, rgb)

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Survival probability",
            font_size=14,
            xaxis_title_font_size=18,
            yaxis_title_font_size=18,
        )

        return fig
