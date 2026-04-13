"""Predefined plots."""

from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aignostics_tme_studio.styling.styling_utils import aignx_colors


def _format_title(title: str | None = None, subtitle: str | None = None) -> str:
    """Format a plot title, optionally appending a subtitle with column info.

    Args:
        title: Main title text. If given, prefixed with "Distribution of".
        subtitle: Column name(s) shown as a sub-line below the title.

    Returns:
        Formatted title string for use in a Plotly layout.
    """
    title = f"Distribution of {title}".capitalize() if title else ""

    if subtitle:
        title += f"<br><sub>Data from column(s): {subtitle}</sub>"
    return title


def _apply_layout(fig: go.Figure, xtitle: str = "", ytitle: str = "", title: str = "", subtitle: str = "") -> go.Figure:
    """Standard formatting of the distribution plot.

    Format axes, font size, add title and subtitle.

    Returns:
        The same figure with an updated layout.
    """
    title = _format_title(title, subtitle)

    fig.update_layout(
        title={"text": title},
        xaxis_title={"text": xtitle, "font_size": 16},
        yaxis_title={"text": ytitle, "font_size": 16},
        legend_title="",
        yaxis_tickformat=".2g",
        font_size=14,
    )
    fig.update_layout(margin_t=120)
    return fig


def _silverman_bandwidth(data: pd.Series) -> float:
    """Automated bandwidth computation for violin plot.

    Ensures all violin plots have similar amounts of width and detail.

    Returns:
        The Silverman bandwidth.
    """
    n = len(data)
    std = data.std()
    return 1.06 * std * n ** (-1 / 5)


def plot_distribution(
    df: pd.DataFrame,
    plot_type: Literal["box", "strip", "violin"] = "box",
    grouping_column: str | None = None,
    **layout_kwargs,
) -> go.Figure:
    """Render the plot as a marimo UI element.

    Args:
        df: The dataframe containing the data to plot. All dataframe columns will
            be plotted on the x-axis, one distribution for each column. If the
            `grouping_column` if given, one series is plotted for each group.
        plot_type: One of "box", "violin" or "strip".
        grouping_column: If given, group data by this column and plot one series
            for each unique value in the column.
        **layout_kwargs: Keyword args to label plot and set titles.

    layout_kwargs:
        title: Title to print above the plot.
        subtitle: Subtitle to print above the plot, below the title.
        xtitle: Label to use on the x-axis.
        ytitle: Label to use on the y-axis.

    Raises:
        ValueError: If plot_type is not available.
    """
    # plotly expects dataframe in long form
    df = df.melt(var_name="var", value_name="value", id_vars=grouping_column)

    df = df.sort_values(by="var")
    if grouping_column:
        df = df.sort_values(by=grouping_column)

    if plot_type == "box":
        fig = px.box(df, x="var", y="value", color=grouping_column, color_discrete_sequence=aignx_colors)
    elif plot_type == "strip":
        fig = px.strip(df, x="var", y="value", color=grouping_column, color_discrete_sequence=aignx_colors)
    elif plot_type == "violin":
        fig = px.violin(
            df,
            x="var",
            y="value",
            color=grouping_column,
            color_discrete_sequence=aignx_colors,
            box=True,
            points="outliers",
        )
        fig.update_traces(bandwidth=_silverman_bandwidth(df["value"]))
    else:
        msg = f"Unknown plot_type {plot_type}."
        raise ValueError(msg)

    return _apply_layout(fig, **layout_kwargs)
