"""Inflamed / excluded / desert (IDE) immune-phenotype survival analysis on OpenTME features.

Reproduces the tumor-immunology blog analysis: a two-threshold rule on lymphocyte density (in
carcinoma vs. stroma) partitions patients into the three immune phenotypes, which are then tested
against overall survival with a three-group log-rank test and pairwise Cox models against the
inflamed (infiltrated) reference.

The pipeline is deliberately small and side-effect free so it can be unit tested and reused across
the ``ide_immune_phenotyping`` notebook and any downstream scans:

    1. :func:`restrict_to_primary_tumors` - keep primary solid tumors only.
    2. :func:`aggregate_slides_to_patient` - average a patient's slides to one profile.
    3. :func:`prepare_overall_survival` - parse survival, drop neoadjuvant-pretreated cases.
    4. :func:`three_group_logrank_pvalue` / :func:`cox_hazard_ratios_vs_reference` - the tests.
"""

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import multivariate_logrank_test

from .cbioportal import OS_MONTHS_COLUMN, OS_STATUS_COLUMN
from .config import NEOADJUVANT_COLUMN

# TCGA barcode: TCGA-<tss>-<patient>-<sample-type><vial>-...; the 4th block's leading two digits are
# the sample-type code (01=primary solid tumor, 02=recurrent, 06=metastatic, 11=solid normal).
PRIMARY_TUMOR_SAMPLE_TYPE_CODE = "01"
_SAMPLE_TYPE_PATTERN = r"^TCGA-[^-]+-[^-]+-(\d{2})"

DURATION_COLUMN = "duration"
EVENT_COLUMN = "event"

INFLAMED = "inflamed"
EXCLUDED = "excluded"
DESERT = "desert"
IDE_PHENOTYPES = (INFLAMED, EXCLUDED, DESERT)

# OpenTME whole-tumor-region (WTR) lymphocyte readouts used by the blog's core-vs-margin IDE rule
# (found in the ``whole_tumor_region_cell_features_*`` files). Densities are in cells/mm²; the paired
# counts let us pool slides -> patient by summed count / summed area (see pooled_zone_density).
LYMPHOCYTE_DENSITY_TUMOR_CORE = "CELL_DENSITY_LYMPHOCYTE_IN_TUMOR_CORE"
LYMPHOCYTE_DENSITY_OUTER_MARGIN = "CELL_DENSITY_LYMPHOCYTE_IN_OUTER_INVASIVE_MARGIN"
LYMPHOCYTE_COUNT_TUMOR_CORE = "CELL_COUNT_LYMPHOCYTE_IN_TUMOR_CORE"
LYMPHOCYTE_COUNT_OUTER_MARGIN = "CELL_COUNT_LYMPHOCYTE_IN_OUTER_INVASIVE_MARGIN"

# Minimum group size for a Cox model to be reported; below this the estimate is too unstable.
_MIN_COX_GROUP_SIZE = 8


def restrict_to_primary_tumors(df: pd.DataFrame, file_name_column: str = "TCGA_FILE_NAME") -> pd.DataFrame:
    """Keep only primary solid tumor slides, dropping recurrent/metastatic/normal samples.

    Several cohorts carry stray non-primary slides whose non-tumor tissue or pre/post-treatment
    effects would confound the immune-phenotype survival readout.

    Args:
        df: Slide-level OpenTME features including the TCGA file-name column.
        file_name_column: Name of the column holding the TCGA barcode / file name.

    Returns:
        The subset of ``df`` whose sample-type code is primary solid tumor (``01``).
    """
    sample_type_code = df[file_name_column].astype(str).str.extract(_SAMPLE_TYPE_PATTERN)[0]
    return df[sample_type_code == PRIMARY_TUMOR_SAMPLE_TYPE_CODE]


def aggregate_slides_to_patient(df: pd.DataFrame, case_id_column: str = "TCGA_CASE_ID") -> pd.DataFrame:
    """Collapse multiple slides per patient into a single profile.

    Numeric features are averaged across the patient's slides; non-numeric columns take the first
    value. Aggregating to the patient before any statistics ensures that patients, not slides, are
    the unit of analysis.

    Args:
        df: Slide-level features containing the case-id column.
        case_id_column: Name of the column identifying the patient (TCGA case id).

    Returns:
        One row per patient with averaged numeric features.
    """
    numeric_columns = df.select_dtypes("number").columns.tolist()
    other_columns = [c for c in df.columns if c not in numeric_columns and c != case_id_column]

    # Aggregate numeric and non-numeric blocks separately, then join once. Building the result with a
    # single concat avoids the column-by-column insertion that fragments wide OpenTME frames (which
    # can carry thousands of columns) and triggers pandas' PerformanceWarning.
    grouped = df.groupby(case_id_column, sort=False)
    # .copy() de-fragments the concatenated block manager before reset_index inserts the key column,
    # avoiding pandas' PerformanceWarning on very wide OpenTME frames (thousands of columns).
    aggregated = pd.concat([grouped[numeric_columns].mean(), grouped[other_columns].first()], axis=1).copy()
    return aggregated.reset_index()


def prepare_overall_survival(df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Parse overall survival, drop neoadjuvant-pretreated cases, and require complete features.

    ``OS_STATUS`` arrives as ``"1:DECEASED"`` / ``"0:LIVING"``; the leading integer is the event
    indicator and ``OS_MONTHS`` the follow-up time. Cases imaged after neoadjuvant therapy are
    removed so pre/post-treatment tissue cannot confound the readout.

    Args:
        df: Patient-level features already merged with cBioPortal survival columns.
        feature_columns: Feature columns that must be non-null for a patient to be included.

    Returns:
        A copy of ``df`` with numeric ``duration`` and ``event`` columns and complete data.
    """
    prepared = df.dropna(subset=[OS_MONTHS_COLUMN, OS_STATUS_COLUMN, *feature_columns]).copy()

    if NEOADJUVANT_COLUMN in prepared.columns:
        neoadjuvant = prepared[NEOADJUVANT_COLUMN].astype(str).str.startswith("Yes")
        prepared = prepared[~neoadjuvant].copy()

    prepared[DURATION_COLUMN] = pd.to_numeric(prepared[OS_MONTHS_COLUMN], errors="coerce")
    prepared[EVENT_COLUMN] = prepared[OS_STATUS_COLUMN].astype(str).str.split(":").str[0].astype(int)
    return prepared.dropna(subset=[DURATION_COLUMN])


def pooled_zone_density(
    df: pd.DataFrame,
    count_column: str,
    density_column: str,
    case_id_column: str = "TCGA_CASE_ID",
    min_area_mm2: float = 0.0,
) -> pd.Series:
    """Pool a zone's per-slide lymphocyte density to one value per patient by area-weighting.

    Averaging per-slide densities over-weights small slides. Instead we recover each slide's zone
    area as ``count / density`` and take ``sum(count) / sum(area)`` across the patient's slides -- the
    same slides->patient pooling the blog performs from raw counts and areas. Slides with no
    lymphocytes contribute a zero count (their area is unrecoverable from a zero density and is
    dropped); a patient whose slides are all lymphocyte-free gets a density of zero.

    A quality gate drops patients whose pooled zone area is below ``min_area_mm2``: a sub-mm² band
    makes ``count / area`` numerically unstable (a handful of cells implies an enormous density) and
    can spuriously flip a patient's phenotype. Such patients are returned as NaN so downstream
    ``prepare_overall_survival`` excludes them.

    Args:
        df: Slide-level features with the zone's count and density columns and a case-id column.
        count_column: Lymphocyte count column for the zone.
        density_column: Lymphocyte density column for the zone (cells/mm²).
        case_id_column: Column identifying the patient.
        min_area_mm2: Minimum pooled zone area (mm²) required to trust the density; 0 disables the gate.

    Returns:
        Per-patient pooled density, indexed by ``case_id_column`` (NaN where the area gate fails).
    """
    slide_area = df[count_column] / df[density_column].replace(0, np.nan)  # cells / (cells/mm²) = mm²
    grouped = pd.DataFrame({
        case_id_column: df[case_id_column].to_numpy(),
        "_count": df[count_column].to_numpy(),
        "_area": slide_area.to_numpy(),
    }).groupby(case_id_column)
    total_count = grouped["_count"].sum(min_count=1)
    total_area = grouped["_area"].sum(min_count=1)
    density = total_count / total_area
    density = density.where(total_area >= min_area_mm2, np.nan)  # drop untrustworthy sub-min-area zones
    return density.mask(total_count == 0, 0.0)  # lymphocyte-free -> density 0 (kept), not 0/0=NaN


def zone_lymphocyte_density(df: pd.DataFrame, count_column: str, area_column: str) -> pd.Series:
    """Compute per-patient lymphocyte density (cells/mm²) for a whole-tumor-region zone.

    A convenience for deriving density from a zone's lymphocyte count and area when a ready-made
    ``CELL_DENSITY_LYMPHOCYTE_IN_<zone>`` column is not available. Because a patient's slides are
    averaged beforehand, dividing the mean count by the mean area equals pooling across slides.

    Args:
        df: Patient-level features containing the zone count and area columns.
        count_column: Column with the lymphocyte count in the zone.
        area_column: Column with the zone's absolute area (μm²); the result carries the input units.

    Returns:
        The lymphocyte density per patient, aligned to ``df``'s index.
    """
    return df[count_column] / df[area_column]


def classify_two_threshold(
    primary: pd.Series,
    secondary: pd.Series,
    primary_threshold: float,
    secondary_threshold: float,
) -> pd.Series:
    """Apply the two-threshold IDE rule to any pair of infiltration features.

    The rule reads top-down: above the ``primary`` threshold is *inflamed*; otherwise above the
    ``secondary`` threshold is *excluded*; otherwise *desert*. For the whole-tumor-region variant the
    primary axis is tumor-core density and the secondary is outer-invasive-margin density.

    Args:
        primary: Primary infiltration feature (e.g. tumor-core lymphocyte density).
        secondary: Secondary feature checked only when the primary threshold is not met.
        primary_threshold: Cutpoint on the primary feature (inflamed above it).
        secondary_threshold: Cutpoint on the secondary feature (excluded above it).

    Returns:
        The IDE phenotype label per patient, aligned to ``primary``'s index.
    """
    phenotype = np.where(
        primary > primary_threshold,
        INFLAMED,
        np.where(secondary > secondary_threshold, EXCLUDED, DESERT),
    )
    return pd.Series(phenotype, index=primary.index)


def median_thresholds(primary: pd.Series, secondary: pd.Series) -> tuple[float, float]:
    """Pre-specified IDE cutpoints: primary median, then secondary median within the non-inflamed set.

    The primary (tumor-core) threshold is the cohort median, so exactly half the patients are
    inflamed. The secondary (outer-margin) threshold is the median **among the non-inflamed**
    patients (primary <= core threshold), so the remaining half splits evenly into excluded and
    desert -- a balanced 50 / 25 / 25 partition. Both cuts are fixed before survival is examined
    (the secondary median is defined purely by the primary split), so the log-rank carries no
    cutpoint-selection bias.

    Args:
        primary: Primary infiltration feature (tumor-core lymphocyte density).
        secondary: Secondary feature (outer-margin lymphocyte density).

    Returns:
        The ``(primary_threshold, secondary_threshold)`` pair.
    """
    primary_threshold = float(primary.median())
    non_inflamed = primary <= primary_threshold
    secondary_threshold = float(secondary[non_inflamed].median())
    return primary_threshold, secondary_threshold


def three_group_logrank_pvalue(duration: pd.Series, event: pd.Series, phenotype: pd.Series) -> float:
    """Return the p-value of the three-group (inflamed/excluded/desert) log-rank test.

    Args:
        duration: Follow-up time per patient.
        event: Event indicator per patient (1 = death, 0 = censored).
        phenotype: IDE phenotype label per patient.

    Returns:
        The log-rank p-value across the three phenotype groups.
    """
    return float(multivariate_logrank_test(duration, phenotype, event).p_value)


def cox_hazard_ratio(group: pd.Series, duration: pd.Series, event: pd.Series) -> dict | None:
    """Fit a Cox model for a binary group indicator and return its hazard ratio.

    Args:
        group: Boolean/0-1 membership per patient (the group whose risk is estimated).
        duration: Follow-up time per patient.
        event: Event indicator per patient (1 = death, 0 = censored).

    Returns:
        A mapping with ``hr``, ``ci_lower``, ``ci_upper`` and ``p``, or ``None`` when either arm has
        too few patients or events for a stable estimate.
    """
    model_df = pd.DataFrame({
        "group": np.asarray(group).astype(int),
        DURATION_COLUMN: np.asarray(duration, dtype=float),
        EVENT_COLUMN: np.asarray(event, dtype=float),
    }).dropna()

    if (
        model_df[EVENT_COLUMN].sum() < _MIN_COX_GROUP_SIZE
        or model_df["group"].sum() < _MIN_COX_GROUP_SIZE
        or (model_df["group"] == 0).sum() < _MIN_COX_GROUP_SIZE
    ):
        return None

    fitted = CoxPHFitter().fit(model_df, DURATION_COLUMN, EVENT_COLUMN)
    confidence = np.exp(fitted.confidence_intervals_.iloc[0])
    return {
        "hr": float(np.exp(fitted.params_["group"])),
        "ci_lower": float(confidence.iloc[0]),
        "ci_upper": float(confidence.iloc[1]),
        "p": float(fitted.summary.loc["group", "p"]),
    }


def cox_hazard_ratios_vs_reference(
    phenotype: pd.Series,
    duration: pd.Series,
    event: pd.Series,
    reference: str = INFLAMED,
) -> pd.DataFrame:
    """Fit pairwise Cox models for each non-reference phenotype against the reference group.

    Each comparison is restricted to the two groups involved (target vs. reference), mirroring the
    blog's "each non-infiltrated group vs. the inflamed group" hazard ratios.

    Args:
        phenotype: IDE phenotype label per patient.
        duration: Follow-up time per patient.
        event: Event indicator per patient (1 = death, 0 = censored).
        reference: The phenotype used as the reference (baseline) group.

    Returns:
        A dataframe indexed by target phenotype with columns ``hr``, ``ci_lower``, ``ci_upper`` and
        ``p``. Comparisons with too few patients or events are omitted.
    """
    reference_mask = phenotype == reference
    rows = {}
    for target in (group for group in IDE_PHENOTYPES if group != reference):
        target_mask = phenotype == target
        subset = target_mask | reference_mask
        result = cox_hazard_ratio(target_mask[subset], duration[subset], event[subset])
        if result is not None:
            rows[target] = result

    return pd.DataFrame.from_dict(rows, orient="index", columns=["hr", "ci_lower", "ci_upper", "p"])


def benjamini_hochberg(pvalues: pd.Series) -> pd.Series:
    """Return Benjamini-Hochberg adjusted q-values, controlling the false-discovery rate.

    Used to account for testing the immune phenotype across several indications at once.

    Args:
        pvalues: Raw p-values indexed by cohort (or any label).

    Returns:
        The adjusted q-values, aligned to the input index and clipped to at most 1.
    """
    ordered = pvalues.sort_values()
    n = len(ordered)
    ranks = np.arange(1, n + 1)
    raw_q = ordered.to_numpy() * n / ranks
    monotone_q = np.minimum.accumulate(raw_q[::-1])[::-1]  # enforce non-decreasing q along the ranking
    return pd.Series(np.minimum(monotone_q, 1.0), index=ordered.index).reindex(pvalues.index)
