import numpy as np
import pandas as pd
import pytest

from aignostics_tme_studio.plotting import distributions


@pytest.fixture(name="dummy_df")
def create_dummy_df() -> pd.DataFrame:
    """Create dummy df."""
    gen = np.random.default_rng(42)
    n = 20
    columns = ["Carcinoma cell", "Lymphocye", "Fibroblast"]
    data = gen.standard_normal(size=(n, len(columns)))
    return pd.DataFrame(data=data, columns=columns)


@pytest.mark.parametrize("grouped", [True, False])
@pytest.mark.parametrize("plot_type", ["box", "strip", "violin"])
@pytest.mark.unit
def test_plot_distribution(dummy_df, plot_type, grouped) -> None:
    """Test distribution plot function generates a figure."""
    group = None
    if grouped:
        group = "group"
        gen = np.random.default_rng(42)
        dummy_df[group] = gen.binomial(len(dummy_df), p=0.5)

    fig = distributions.plot_distribution(df=dummy_df, plot_type=plot_type, grouping_column=group)

    feature_cols = {col for col in dummy_df.columns if col != "group"}

    assert set(fig.data[0].x) == feature_cols
    assert fig.data[0].y.size == len(dummy_df) * len(feature_cols)


@pytest.mark.unit
def test_plot_distribution_layout(dummy_df) -> None:
    """Test distribution plot function applies layout correctly."""
    layout_kwargs = {
        "xtitle": "test_x_title",
        "ytitle": "test_y_title",
        "subtitle": "test_sub_title",
        "title": "test_title",
    }
    fig = distributions.plot_distribution(df=dummy_df, plot_type="box", **layout_kwargs)
    assert fig.layout.title.text == "Distribution of test_title<br><sub>Data from column(s): test_sub_title</sub>"
    assert fig.layout.xaxis.title.text == "test_x_title"
    assert fig.layout.yaxis.title.text == "test_y_title"
