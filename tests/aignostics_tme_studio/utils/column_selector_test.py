"""Test module for the ColumnSelector element."""

import numpy as np
import pandas as pd
import pytest

from aignostics_tme_studio.utils import column_selector, data_classes, utils

MODEL_CONFIG = {
    "cell_cls": ["Carcinoma Cell", "Stroma", "Lymphocyte", "Macrophage"],
    "tissue_cls": ["Carcinoma", "Stroma", "Necrosis"],
}

TISSUE_STAT = data_classes.Feature(name="Relative Area", formatter="RELATIVE_AREA_{tissue_cls}", unit="%")
CELL_IN_TISSUE_STAT = data_classes.Feature(name="Density", formatter="DENSITY_OF_{cell_cls}_{tissue_cls}", unit="")


@pytest.fixture(name="dummy_df")
def create_dummy_df() -> pd.DataFrame:
    """Create a dummy dataframe with columns corresponding to the model output classes and features."""
    gen = np.random.default_rng(seed=42)
    columns = []
    for tissue_cls in MODEL_CONFIG["tissue_cls"]:
        columns.extend([
            f"DENSITY_OF_{utils.to_allcaps(cell_cls)}_{utils.to_allcaps(tissue_cls)}"
            for cell_cls in MODEL_CONFIG["cell_cls"]
        ])
        columns.append(f"RELATIVE_AREA_{utils.to_allcaps(tissue_cls)}")

    columns.extend([f"DENSITY_OF_{utils.to_allcaps(cell_cls)}" for cell_cls in MODEL_CONFIG["cell_cls"]])

    # fill columns with dummy data
    data = {col: gen.uniform(size=10) for col in columns}
    return pd.DataFrame(data)


@pytest.mark.unit
def test_column_selector_get_column_format(dummy_df) -> None:
    """Test that get_column_format correctly fills in the formatter string."""
    selector = column_selector.FeatureColumnSelector(
        features=[TISSUE_STAT],
        x_variable="tissue_cls",
        model_config=MODEL_CONFIG,
    )
    dropdowns = selector.render_dropdowns()

    # 1 dropdown for selecting feature.
    # Since `tissue_cls` is the x variable, we don't need a dropdown for it.
    assert len(dropdowns.value) == 1

    df = selector.extract_feature_columns(df=dummy_df, **dropdowns.value)
    assert len(df) == len(dummy_df)
    assert df.shape[1] == len(MODEL_CONFIG["tissue_cls"])


@pytest.mark.unit
def test_column_selector_multiple_formatters(dummy_df) -> None:
    """Test that get_column_format correctly fills in the formatter string."""
    selector = column_selector.FeatureColumnSelector(
        features=[CELL_IN_TISSUE_STAT],
        x_variable="cell_cls",
        model_config=MODEL_CONFIG,
    )
    dropdowns = selector.render_dropdowns()

    # 1 dropdown for selecting feature, 1 dropdown for selecting tissue type.
    assert len(dropdowns.value) == 2

    df = selector.extract_feature_columns(df=dummy_df, **dropdowns.value)
    assert len(df) == len(dummy_df)
    assert np.all([c in df.columns for c in MODEL_CONFIG["cell_cls"]])


@pytest.mark.unit
def test_column_selector_anuclear_regions() -> None:
    """Test that get_column_format correctly fills in the formatter string for anuclear regions."""
    selector = column_selector.NoAnucleatedAreasFeatureColumnSelector(
        features=[CELL_IN_TISSUE_STAT],
        x_variable="cell_cls",
        model_config=MODEL_CONFIG,
    )
    dropdowns = selector.render_dropdowns()
    assert "Necrosis" not in dropdowns["tissue_cls"].options


@pytest.mark.unit
def test_column_selector_with_all_tissue(dummy_df) -> None:
    """Test that get_column_format correctly fills in the formatter string for anuclear regions."""
    selector = column_selector.CellInTissueFeatureColumnSelector(
        features=[CELL_IN_TISSUE_STAT],
        x_variable="cell_cls",
        model_config=MODEL_CONFIG,
    )
    dropdowns = selector.render_dropdowns()
    vals = dropdowns.value
    vals["tissue_cls"] = None
    df = selector.extract_feature_columns(df=dummy_df, **vals)
    assert np.all([c in df.columns for c in MODEL_CONFIG["cell_cls"]])


@pytest.mark.unit
def test_grouping_column_kept(dummy_df) -> None:
    """Test that the grouping column is kept in the output dataframe."""
    dummy_df["group"] = ["A"] * len(dummy_df)
    selector = column_selector.FeatureColumnSelector(
        features=[CELL_IN_TISSUE_STAT],
        x_variable="cell_cls",
        model_config=MODEL_CONFIG,
    )
    dropdowns = selector.render_dropdowns()
    df = selector.extract_feature_columns(df=dummy_df, **dropdowns.value, grouping_column="group")
    assert "group" in df.columns
