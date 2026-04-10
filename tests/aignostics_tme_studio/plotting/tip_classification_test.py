"""Test module for TIP classifiction."""

import numpy as np
import pandas as pd
import pytest

from aignostics_tme_studio.plotting import tip_classification


@pytest.fixture(name="dummy_df")
def fixture_dummy_df() -> pd.DataFrame:
    """Dummy data."""
    rng = np.random.default_rng(12345)

    return pd.DataFrame({
        tip_classification.COLUMN_DENSITY_CARCINOMA: rng.uniform(0, 1, size=(10,)),
        tip_classification.COLUMN_DENSITY_STROMA: rng.uniform(0, 1, size=(10,)),
        tip_classification.COLUMN_RATIO_CARCINOMA: rng.uniform(0, 1, size=(10,)),
        tip_classification.COLUMN_RATIO_STROMA: rng.uniform(0, 1, size=(10,)),
    })


@pytest.mark.parametrize("metric", ["Percentage", "Density"])
@pytest.mark.unit
def test_ide_classification_update_thresholds(dummy_df, metric) -> None:
    """Check that updating the thresholds updates the TIP classification."""
    tip = tip_classification.TIPClassifier(dummy_df, carcinoma_thresh=0, stroma_thresh=0.3, metric=metric)
    ide = tip.phenotype_classification
    assert len(tip.phenotype_classification) == len(dummy_df)
    assert np.equal(ide, tip.phenotype_classification).all()

    tip.set_thresholds(carcinoma_thresh=1, stroma_thresh=0)
    assert np.not_equal(tip.phenotype_classification, ide).any()


@pytest.mark.parametrize("metric", ["Percentage", "Density"])
@pytest.mark.unit
def test_ide_classification(dummy_df, metric) -> None:
    """Test IDE classification is done correctly."""
    tip = tip_classification.TIPClassifier(dummy_df, carcinoma_thresh=-1, stroma_thresh=0.3, metric=metric)
    assert len(tip.phenotype_classification) == len(dummy_df)

    # all inflamed
    assert (tip.phenotype_classification == "inflamed").sum() == len(dummy_df)

    # all excluded
    tip.set_thresholds(carcinoma_thresh=1, stroma_thresh=-1)
    assert (tip.phenotype_classification == "excluded").sum() == len(dummy_df)

    # all desert
    tip.set_thresholds(carcinoma_thresh=1, stroma_thresh=1)
    assert (tip.phenotype_classification == "desert").sum() == len(dummy_df)

    # Mix of statuses
    tip.set_thresholds(carcinoma_thresh=0.5, stroma_thresh=0.3)

    carc_dens = dummy_df[
        tip_classification.COLUMN_DENSITY_CARCINOMA
        if metric == "Density"
        else tip_classification.COLUMN_RATIO_CARCINOMA
    ]
    strom_dens = dummy_df[
        tip_classification.COLUMN_DENSITY_STROMA if metric == "Density" else tip_classification.COLUMN_RATIO_STROMA
    ]
    assert (tip.phenotype_classification == "inflamed").sum() == (carc_dens >= 0.5).sum()
    assert (tip.phenotype_classification == "excluded").sum() == ((strom_dens >= 0.3) & (carc_dens < 0.5)).sum()


@pytest.mark.unit
def test_plot_ide_classification(dummy_df) -> None:
    """Test the plotter plots all traces."""
    tip = tip_classification.TIPClassifier(dummy_df, carcinoma_thresh=0.5, stroma_thresh=0.5)
    fig = tip.plot_tip_classification()
    assert len(fig.data) == 6
    data_labels = {d["name"] for d in fig.data}
    assert {"excluded", "inflamed", "desert"}.issubset(data_labels)
