"""Unit tests for the IDE immune-phenotype survival analysis."""

import numpy as np
import pandas as pd
import pytest

from aignostics_tme_studio.utils import ide
from aignostics_tme_studio.utils.cbioportal import OS_MONTHS_COLUMN, OS_STATUS_COLUMN
from aignostics_tme_studio.utils.config import NEOADJUVANT_COLUMN

CARCINOMA = "CELL_DENSITY_LYMPHOCYTE_IN_CARCINOMA"
STROMA = "CELL_DENSITY_LYMPHOCYTE_IN_STROMA"


def _barcode(case: str, sample_type: str = "01") -> str:
    return f"TCGA-AA-{case}-{sample_type}Z-00-DX1.HEX"


@pytest.mark.unit
def test_restrict_to_primary_tumors_keeps_only_code_01() -> None:
    """Only primary solid tumor (sample-type 01) slides are retained."""
    df = pd.DataFrame({
        "TCGA_FILE_NAME": [_barcode("0001", "01"), _barcode("0002", "06"), _barcode("0003", "11")],
    })

    result = ide.restrict_to_primary_tumors(df)

    assert list(result["TCGA_FILE_NAME"]) == [_barcode("0001", "01")]


@pytest.mark.unit
def test_aggregate_slides_to_patient_averages_numeric() -> None:
    """Numeric features are averaged per patient; non-numeric columns take the first value."""
    df = pd.DataFrame({
        "TCGA_CASE_ID": ["TCGA-AA-0001", "TCGA-AA-0001", "TCGA-AA-0002"],
        CARCINOMA: [0.2, 0.4, 1.0],
        "TCGA_FILE_NAME": ["slide_a", "slide_b", "slide_c"],
    })

    result = ide.aggregate_slides_to_patient(df).set_index("TCGA_CASE_ID")

    assert result.loc["TCGA-AA-0001", CARCINOMA] == pytest.approx(0.3)
    assert result.loc["TCGA-AA-0002", CARCINOMA] == pytest.approx(1.0)
    assert len(result) == 2


@pytest.mark.unit
def test_prepare_overall_survival_parses_and_filters() -> None:
    """Survival is parsed into duration/event and neoadjuvant-pretreated cases are dropped."""
    df = pd.DataFrame({
        OS_MONTHS_COLUMN: ["12.5", "30.0", "8.0", np.nan],
        OS_STATUS_COLUMN: ["1:DECEASED", "0:LIVING", "1:DECEASED", "0:LIVING"],
        NEOADJUVANT_COLUMN: ["No", "Yes", "No", "No"],
        CARCINOMA: [0.1, 0.2, 0.3, 0.4],
    })

    result = ide.prepare_overall_survival(df, [CARCINOMA])

    # The neoadjuvant "Yes" row and the missing-months row are removed.
    assert len(result) == 2
    assert list(result[ide.EVENT_COLUMN]) == [1, 1]
    assert list(result[ide.DURATION_COLUMN]) == [12.5, 8.0]


@pytest.mark.unit
def test_zone_lymphocyte_density_divides_count_by_area() -> None:
    """Density is the lymphocyte count divided by the zone area, aligned to the input index."""
    count_column, area_column = "CELL_COUNT_LYMPHOCYTE_IN_TUMOR_CORE", "ABSOLUTE_AREA_TUMOR_CORE"
    df = pd.DataFrame({count_column: [100.0, 0.0], area_column: [50.0, 20.0]}, index=["p1", "p2"])

    density = ide.zone_lymphocyte_density(df, count_column, area_column)

    assert list(density.index) == ["p1", "p2"]
    assert density["p1"] == pytest.approx(2.0)
    assert density["p2"] == pytest.approx(0.0)


@pytest.mark.unit
def test_pooled_zone_density_area_weights_across_slides() -> None:
    """Pooling uses summed count / summed area, not the mean of per-slide densities."""
    count, density = "CELL_COUNT_LYMPHOCYTE_IN_TUMOR_CORE", ide.LYMPHOCYTE_DENSITY_TUMOR_CORE
    # Patient p1: slide A (100 cells, density 10 -> area 10) + slide B (100 cells, density 100 -> area 1).
    # Pooled = 200 / 11 = 18.18, unlike the naive mean of densities (55).
    df = pd.DataFrame({
        "TCGA_CASE_ID": ["p1", "p1", "p2"],
        count: [100.0, 100.0, 0.0],
        density: [10.0, 100.0, 0.0],
    })

    pooled = ide.pooled_zone_density(df, count, density)

    assert pooled["p1"] == pytest.approx(200.0 / 11.0)
    assert pooled["p2"] == pytest.approx(0.0)  # lymphocyte-free patient -> density 0, not NaN


@pytest.mark.unit
def test_pooled_zone_density_area_gate() -> None:
    """Patients whose pooled zone area is below min_area_mm2 are dropped (NaN), except lymphocyte-free."""
    count, density = "CELL_COUNT_LYMPHOCYTE_IN_TUMOR_CORE", ide.LYMPHOCYTE_DENSITY_TUMOR_CORE
    # p1 area = 100/50 = 2 mm2 (below gate); p2 area = 100/10 = 10 mm2 (above); p3 lymphocyte-free.
    df = pd.DataFrame({
        "TCGA_CASE_ID": ["p1", "p2", "p3"],
        count: [100.0, 100.0, 0.0],
        density: [50.0, 10.0, 0.0],
    })

    pooled = ide.pooled_zone_density(df, count, density, min_area_mm2=5.0)

    assert np.isnan(pooled["p1"])  # 2 mm2 < 5 mm2 gate -> dropped
    assert pooled["p2"] == pytest.approx(10.0)  # 10 mm2 >= gate -> kept
    assert pooled["p3"] == pytest.approx(0.0)  # lymphocyte-free kept as 0 despite unrecoverable area


@pytest.mark.unit
def test_median_thresholds_balances_non_inflamed_split() -> None:
    """Secondary threshold is the median within the non-inflamed subset -> balanced 50/25/25."""
    core = pd.Series([1.0, 2.0, 3.0, 4.0])  # median 2.5 -> two inflamed (3,4), two non-inflamed (1,2)
    margin = pd.Series([10.0, 30.0, 99.0, 99.0])  # non-inflamed margins are {10,30} -> median 20

    core_thr, margin_thr = ide.median_thresholds(core, margin)
    phenotype = ide.classify_two_threshold(core, margin, core_thr, margin_thr)

    assert core_thr == pytest.approx(2.5)
    assert margin_thr == pytest.approx(20.0)  # median of {10, 30}, not of all four margins
    assert list(phenotype) == [ide.DESERT, ide.EXCLUDED, ide.INFLAMED, ide.INFLAMED]


@pytest.mark.unit
def test_classify_two_threshold_applies_top_down_rule() -> None:
    """The two-threshold rule assigns inflamed, then excluded, then desert."""
    primary = pd.Series([2.0, 0.5, 0.5])  # core density
    secondary = pd.Series([0.0, 2.0, 0.5])  # margin density

    phenotype = ide.classify_two_threshold(primary, secondary, primary_threshold=1.0, secondary_threshold=1.0)

    assert list(phenotype) == [ide.INFLAMED, ide.EXCLUDED, ide.DESERT]


@pytest.mark.unit
def test_prepare_overall_survival_without_neoadjuvant_column() -> None:
    """When the neoadjuvant column is absent, no cases are dropped on that basis."""
    df = pd.DataFrame({
        OS_MONTHS_COLUMN: ["12.5", "30.0"],
        OS_STATUS_COLUMN: ["1:DECEASED", "0:LIVING"],
        CARCINOMA: [0.1, 0.2],
    })

    result = ide.prepare_overall_survival(df, [CARCINOMA])

    assert len(result) == 2


@pytest.fixture(name="cohort")
def fixture_cohort() -> tuple[pd.Series, pd.Series, pd.Series]:
    """A separable cohort where inflamed patients survive markedly longer than the rest."""
    rng = np.random.default_rng(42)
    size = 120
    phenotype = pd.Series(np.repeat(list(ide.IDE_PHENOTYPES), size // 3))
    # Inflamed: long times, mostly censored; others: shorter times, mostly events.
    base = np.where(phenotype == ide.INFLAMED, 90.0, 25.0)
    duration = pd.Series(np.clip(base + rng.normal(0, 5, size), 1, None))
    event = pd.Series(np.where(phenotype == ide.INFLAMED, 0, 1))
    return phenotype, duration, event


@pytest.mark.unit
def test_three_group_logrank_detects_separation(cohort) -> None:
    """A strongly separated cohort yields a significant three-group log-rank p."""
    phenotype, duration, event = cohort

    p_value = ide.three_group_logrank_pvalue(duration, event, phenotype)

    assert 0.0 <= p_value < 0.05


@pytest.mark.unit
def test_cox_hazard_ratio_binary_group(cohort) -> None:
    """A binary high-risk group (non-inflamed) yields a hazard ratio above 1 vs. the rest."""
    phenotype, duration, event = cohort
    group = phenotype != ide.INFLAMED

    result = ide.cox_hazard_ratio(group, duration, event)

    assert result is not None
    assert result["hr"] > 1
    assert result["ci_lower"] <= result["hr"] <= result["ci_upper"]


@pytest.mark.unit
def test_cox_hazard_ratio_returns_none_for_small_group() -> None:
    """Too small a group returns None instead of an unstable estimate."""
    group = pd.Series([True] * 3 + [False] * 30)
    duration = pd.Series(np.linspace(1, 100, len(group)))
    event = pd.Series([1] * len(group))

    assert ide.cox_hazard_ratio(group, duration, event) is None


@pytest.mark.unit
def test_cox_hazard_ratios_vs_reference(cohort) -> None:
    """Non-inflamed groups carry hazard ratios above 1 relative to the inflamed reference."""
    phenotype, duration, event = cohort

    hazard_ratios = ide.cox_hazard_ratios_vs_reference(phenotype, duration, event)

    assert set(hazard_ratios.index) == {ide.EXCLUDED, ide.DESERT}
    assert (hazard_ratios["hr"] > 1).all()
    assert (hazard_ratios["ci_lower"] <= hazard_ratios["hr"]).all()
    assert (hazard_ratios["hr"] <= hazard_ratios["ci_upper"]).all()


@pytest.mark.unit
def test_cox_hazard_ratios_skips_small_groups() -> None:
    """Comparisons with too few patients or events are omitted from the result."""
    phenotype = pd.Series([ide.INFLAMED] * 20 + [ide.EXCLUDED] * 2 + [ide.DESERT] * 2)
    duration = pd.Series(np.linspace(1, 100, len(phenotype)))
    event = pd.Series([1] * len(phenotype))

    hazard_ratios = ide.cox_hazard_ratios_vs_reference(phenotype, duration, event)

    assert hazard_ratios.empty


@pytest.mark.unit
def test_benjamini_hochberg_matches_reference() -> None:
    """BH q-values match a hand-computed reference and preserve the input index order."""
    pvalues = pd.Series({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})

    q = ide.benjamini_hochberg(pvalues)

    assert list(q.index) == ["a", "b", "c", "d"]
    # Ranked: d(0.005), a(0.01), c(0.03), b(0.04); q = p * n / rank with monotone enforcement.
    assert q["d"] == pytest.approx(0.02)
    assert q["a"] == pytest.approx(0.02)
    assert q["c"] == pytest.approx(0.04)
    assert q["b"] == pytest.approx(0.04)
    assert (q <= 1).all()
