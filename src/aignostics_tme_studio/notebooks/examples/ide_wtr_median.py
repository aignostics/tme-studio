import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Show logo
    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()
    return (styling_utils,)


@app.cell(hide_code=True)
def _(styling_utils):
    styling_utils.load_css()


@app.cell(hide_code=True)
def _():
    # Get Hugging Face token
    import marimo as mo

    _md = mo.md("""Enter your hugging face token in the below box to enable access to OpenTME.""")

    _hf_instructions = """Create an access token by going to [hf.co/settings/tokens](https://hf.co/settings/tokens)
        1. Go to "Repositories permissions".
        2. Select "datasets/Aignostics/OpenTME" and check boxes for read and view access.
        3. Click "create token". Enter your hugging face token in the below box to enable access to OpenTME.
                         """
    _acc = mo.accordion({"Click here for instructions to create a Hugging Face token": _hf_instructions})
    hf_token = mo.ui.text(kind="password", label="Your HF Token from hf.co/settings/tokens")
    mo.vstack([_md, _acc, hf_token])
    return hf_token, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # IDE from the whole tumor region (median cut) 🎯

    This notebook reproduces the tumor-immunology blog result
    ([code](https://github.com/aignostics/ide-blog-post)): the **inflamed / excluded / desert (IDE)**
    phenotype built from OpenTME's **whole-tumor-region (WTR)** zone readouts, tested against overall
    survival across eight TCGA cohorts.

    OpenTME resolves each slide into concentric zones (tumor core → inner margin → outer invasive
    margin → extratumoral tissue) and reports a lymphocyte count and area per zone. We build two
    densities straight from that geometry:

    - lymphocyte density in the **tumor core** — lymphocytes that infiltrated the tumor itself.
    - lymphocyte density in the **outer invasive margin** (the 500 μm band just outside the tumor) —
      lymphocytes held at the tumor's leading edge.

    ```python
    lym_core   = df["CELL_DENSITY_LYMPHOCYTE_IN_TUMOR_CORE"]             # cells/mm² in the tumor core
    lym_margin = df["CELL_DENSITY_LYMPHOCYTE_IN_OUTER_INVASIVE_MARGIN"]  # cells/mm² at the outer margin

    core_thresh   = lym_core.median()                              # half the patients are inflamed
    margin_thresh = lym_margin[lym_core <= core_thresh].median()   # split the rest 50/50

    phenotype = np.where(lym_core   > core_thresh,   "inflamed",
                np.where(lym_margin > margin_thresh, "excluded", "desert"))
    ```

    These densities live in OpenTME's `whole_tumor_region_cell_features_*` files. The tumor core is
    cut at the cohort median (so half the patients are inflamed); the outer margin is then cut at its
    median *within the non-inflamed patients*, giving a balanced 50 / 25 / 25 split. Both cuts are
    fixed before survival is examined, so the log-rank p carries no cutpoint-selection bias. A patient's
    slides are pooled by summed count / summed area, and a quality gate drops patients whose core or
    margin band is below ~5 mm² (unreliable density). Survival endpoints are not part of OpenTME; we
    link them by TCGA barcode and fetch harmonized overall survival from
    [cBioPortal](https://www.cbioportal.org/).
    """)


@app.cell(hide_code=True)
def _():
    # Shared imports and the tumor-core / outer-margin density column names.
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.plotting.tip_classification import IDE_COLORS
    from aignostics_tme_studio.utils import cbioportal, config, ide, utils

    ide_colors = IDE_COLORS  # lowercase alias so it can be passed between marimo cells
    core_density = ide.LYMPHOCYTE_DENSITY_TUMOR_CORE
    margin_density = ide.LYMPHOCYTE_DENSITY_OUTER_MARGIN
    return (
        cbioportal,
        config,
        core_density,
        hf_hub_download,
        ide,
        ide_colors,
        margin_density,
        pd,
        utils,
    )


@app.cell(hide_code=True)
def _(config, mo):
    _md = mo.md("""Select a TCGA indication, and the minimum trustworthy zone area (quality gate).""")
    indication = mo.ui.dropdown(
        options=list(config.CBIOPORTAL_STUDIES), value=config.DEFAULT_INDICATION, label="Indication"
    )
    # Drop patients whose pooled tumor-core or outer-margin band is below this area: a sub-mm² zone
    # makes count/area density numerically unstable. 5 mm² removes the pathological tail.
    min_area = mo.ui.slider(
        start=0, stop=20, step=1, value=5, label="Min. zone area (mm²) quality gate", include_input=True
    )
    mo.vstack([_md, indication, min_area])
    return indication, min_area


@app.cell
def _(
    cbioportal,
    config,
    core_density,
    hf_hub_download,
    hf_token,
    ide,
    margin_density,
    min_area,
    pd,
    utils,
):
    def build_cohort(indication_name):
        """Load WTR features from HF, pool core/margin densities, join survival, cut at the median.

        Returns the prepared patient-level dataframe, the IDE phenotype per patient, and the two
        median thresholds used for the boundary lines.
        """
        # 1. Whole-tumor-region cell features, restricted to primary tumors.
        path = hf_hub_download(
            repo_id=config.REPO_ID,
            filename=utils.get_wtr_cell_features_file_for_indication(indication_name),
            repo_type="dataset",
            token=hf_token.value or None,
        )
        slides = ide.restrict_to_primary_tumors(pd.read_csv(path))

        # 2. Pool each patient's slides to one density per zone (summed count / summed area), rather
        #    than averaging per-slide densities -- this is the correct area-weighted aggregation.
        #    The min_area gate drops patients with a sub-threshold (unreliable) zone band.
        patients = pd.DataFrame({
            core_density: ide.pooled_zone_density(
                slides, ide.LYMPHOCYTE_COUNT_TUMOR_CORE, core_density, min_area_mm2=min_area.value
            ),
            margin_density: ide.pooled_zone_density(
                slides, ide.LYMPHOCYTE_COUNT_OUTER_MARGIN, margin_density, min_area_mm2=min_area.value
            ),
        }).reset_index()

        # 3. Join harmonized overall survival and require complete data.
        merged = patients.merge(
            cbioportal.load_survival(config.CBIOPORTAL_STUDIES[indication_name]),
            left_on="TCGA_CASE_ID",
            right_on=cbioportal.PATIENT_ID_COLUMN,
            how="inner",
        )
        prepared = ide.prepare_overall_survival(merged, [core_density, margin_density])

        # 4. Pre-specified thresholds: core median, then outer-margin median WITHIN the non-inflamed
        #    subset -> balanced 50/25/25 inflamed/excluded/desert. (Interactive sliders start here.)
        core_median, margin_median = ide.median_thresholds(prepared[core_density], prepared[margin_density])
        phenotype = ide.classify_two_threshold(
            prepared[core_density], prepared[margin_density], core_median, margin_median
        )
        return prepared, phenotype, core_median, margin_median

    return (build_cohort,)


@app.cell
def _(build_cohort, cbioportal, indication, mo):
    df_ide, _, core_median, margin_median = build_cohort(indication.value)

    mo.vstack([
        mo.md(f"""**{len(df_ide)}** patients with WTR features and survival for `{indication.value}`
        ({int(df_ide["event"].sum())} deaths)."""),
        df_ide[
            [
                "TCGA_CASE_ID",
                cbioportal.OS_MONTHS_COLUMN,
                cbioportal.OS_STATUS_COLUMN,
            ]
        ].head(),
    ])
    return core_median, df_ide, margin_median


@app.cell(hide_code=True)
def _(core_density, core_median, df_ide, margin_density, margin_median, mo):
    # Interactive controls: drag the two thresholds (default = cohort median), pick the survival
    # comparison, and clip the follow-up window.
    def _slider(series, default, label):
        return mo.ui.slider(
            start=float(series.min()),
            stop=float(series.max()),
            step=(float(series.max()) - float(series.min())) / 200 or 1e-6,
            value=float(default),
            label=label,
            include_input=True,
            full_width=True,
        )

    core_threshold = _slider(df_ide[core_density], core_median, "Tumor-core threshold (inflamed above)")
    margin_threshold = _slider(df_ide[margin_density], margin_median, "Outer-margin threshold (excluded above)")
    comparison = mo.ui.dropdown(
        options=["Three groups", "inflamed vs rest", "excluded vs rest", "desert vs rest"],
        value="Three groups",
        label="Survival comparison",
    )
    clip_months = mo.ui.slider(
        start=12, stop=120, step=12, value=120, label="Clip follow-up (months)", include_input=True
    )

    mo.vstack([
        mo.md("### Controls"),
        core_threshold,
        margin_threshold,
        mo.hstack([comparison, clip_months], justify="start", gap=2),
    ])
    return clip_months, comparison, core_threshold, margin_threshold


@app.cell
def _(core_density, core_threshold, df_ide, ide, margin_density, margin_threshold):
    # Recompute the phenotype from the (possibly dragged) thresholds -- everything downstream reacts.
    phenotype = ide.classify_two_threshold(
        df_ide[core_density], df_ide[margin_density], core_threshold.value, margin_threshold.value
    )
    return (phenotype,)


@app.cell
def _(
    core_density,
    core_threshold,
    df_ide,
    ide,
    ide_colors,
    indication,
    margin_density,
    margin_threshold,
    mo,
    phenotype,
):
    import numpy as np
    import plotly.graph_objects as go

    _x, _y = df_ide[core_density], df_ide[margin_density]
    _ct, _mt = core_threshold.value, margin_threshold.value
    # Clip the view at the 99th percentile so a few extreme densities don't flatten the cloud.
    _xmax = max(float(np.nanquantile(_x, 0.99)), _ct * 1.05)
    _ymax = max(float(np.nanquantile(_y, 0.99)), _mt * 1.05)

    def _rgba(hex_color, alpha):
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({r},{g},{b},{alpha})"

    _fig = go.Figure()
    _fig.update_layout(
        title=f"{indication.value} — tumor core vs. outer invasive margin",
        xaxis_title="Tumor-core lymphocytes (cells/mm²)",
        yaxis_title="Outer-margin lymphocytes (cells/mm²)",
        template="simple_white",
        hovermode="closest",
        hoverlabel={"namelength": -1},
        xaxis_range=[0, _xmax],
        yaxis_range=[0, _ymax],
    )
    # Faint phenotype-colored region backgrounds, drawn under the points.
    _fig.add_shape(
        type="rect",
        x0=0,
        x1=_ct,
        y0=0,
        y1=_mt,
        layer="below",
        line_width=0,
        fillcolor=_rgba(ide_colors[ide.DESERT], 0.15),
    )
    _fig.add_shape(
        type="rect",
        x0=0,
        x1=_ct,
        y0=_mt,
        y1=_ymax,
        layer="below",
        line_width=0,
        fillcolor=_rgba(ide_colors[ide.EXCLUDED], 0.15),
    )
    _fig.add_shape(
        type="rect",
        x0=_ct,
        x1=_xmax,
        y0=0,
        y1=_ymax,
        layer="below",
        line_width=0,
        fillcolor=_rgba(ide_colors[ide.INFLAMED], 0.15),
    )
    # Core threshold spans the plot; the margin threshold only separates excluded/desert to its left.
    _fig.add_shape(type="line", x0=_ct, x1=_ct, y0=0, y1=_ymax, line={"dash": "dash", "color": "#8a91a8", "width": 1})
    _fig.add_shape(type="line", x0=0, x1=_ct, y0=_mt, y1=_mt, line={"dash": "dash", "color": "#8a91a8", "width": 1})
    for _group in ide.IDE_PHENOTYPES:
        _mask = phenotype == _group
        _fig.add_scatter(
            x=_x[_mask],
            y=_y[_mask],
            mode="markers",
            name=f"{_group} (n={int(_mask.sum())})",
            marker={"color": ide_colors[_group], "size": 6, "opacity": 0.8, "line_width": 0},
            hovertemplate="tumor core %{x:.0f} cells/mm²<br>outer margin %{y:.0f} cells/mm²<extra></extra>",
        )
    mo.ui.plotly(_fig)


@app.cell
def _(comparison, df_ide, ide, ide_colors, pd, phenotype):
    # Map the comparison choice to per-patient labels, colors, log-rank p and a Cox table.
    _duration, _event = df_ide[ide.DURATION_COLUMN], df_ide[ide.EVENT_COLUMN]

    if comparison.value == "Three groups":
        labels = phenotype
        label_colors = dict(ide_colors)
        hr = ide.cox_hazard_ratios_vs_reference(phenotype, _duration, _event)
        caption = "### Hazard ratios vs. inflamed (reference)"
    else:
        _target = comparison.value.split()[0]
        labels = phenotype.where(phenotype == _target, "rest")
        label_colors = {_target: ide_colors[_target], "rest": "#9aa0ae"}
        _row = ide.cox_hazard_ratio(phenotype == _target, _duration, _event)
        hr = pd.DataFrame({_target: _row}).T if _row else pd.DataFrame(columns=["hr", "ci_lower", "ci_upper", "p"])
        caption = f"### Hazard ratio: {_target} vs. rest"

    logrank_p = ide.three_group_logrank_pvalue(_duration, _event, labels)
    return caption, hr, label_colors, labels, logrank_p


@app.cell
def _(caption, clip_months, df_ide, hr, ide, label_colors, labels, logrank_p, mo):
    from lifelines import KaplanMeierFitter

    from aignostics_tme_studio.plotting import kaplan_meier

    _duration, _event = df_ide[ide.DURATION_COLUMN], df_ide[ide.EVENT_COLUMN]

    def _fit(group):
        mask = labels == group
        return KaplanMeierFitter().fit(
            durations=_duration[mask].clip(upper=clip_months.value),
            event_observed=_event[mask],
            label=f"{group} (n={int(mask.sum())})",
        )

    _order = [g for g in [*ide.IDE_PHENOTYPES, "rest"] if (labels == g).any()]
    _color_map = {f"{g} (n={int((labels == g).sum())})": label_colors[g] for g in _order}
    _figure = kaplan_meier.KaplanMeierPlotter(show_censors=True).render([_fit(g) for g in _order], color_map=_color_map)

    _hr_table = (
        hr.assign(**{"95% CI": hr.apply(lambda r: f"{r['ci_lower']:.2f}-{r['ci_upper']:.2f}", axis=1)})[
            ["hr", "95% CI", "p"]
        ].round(3)
        if not hr.empty
        else hr
    )

    _star = "★" if logrank_p < 0.05 else ""
    mo.vstack([
        mo.md(f"**Log-rank p = {logrank_p:.4f}** {_star} (follow-up clipped at {clip_months.value} months)"),
        mo.ui.plotly(_figure),
        mo.md(caption),
        mo.md(_hr_table.to_markdown() if not _hr_table.empty else "_Too few patients/events for a stable estimate._"),
    ])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Across cohorts

    The headline result: the pre-specified median cut run across every indication, with a
    Benjamini-Hochberg correction for testing them all at once. **★** marks log-rank p < 0.05.
    Press the button to download and analyze every cohort.
    """)
    run_all = mo.ui.run_button(label="Run all indications")
    run_all
    return (run_all,)


@app.cell
def _(build_cohort, config, ide, mo, pd, run_all):
    mo.stop(not run_all.value, mo.md("*Press the button above to compute the cross-cohort summary.*"))

    def _summarize(indication_name):
        cohort_df, cohort_phenotype, _, _ = build_cohort(indication_name)
        return {
            "cohort": indication_name,
            "patients": len(cohort_df),
            "events": int(cohort_df[ide.EVENT_COLUMN].sum()),
            "logrank_p": ide.three_group_logrank_pvalue(
                cohort_df[ide.DURATION_COLUMN], cohort_df[ide.EVENT_COLUMN], cohort_phenotype
            ),
        }

    summary = pd.DataFrame([_summarize(name) for name in config.CBIOPORTAL_STUDIES]).set_index("cohort")
    summary["q_value"] = ide.benjamini_hochberg(summary["logrank_p"])
    summary["★"] = summary["logrank_p"].map(lambda p: "★" if p < 0.05 else "")

    mo.vstack([
        mo.md("### Three-group log-rank across cohorts (median WTR cut, BH-corrected)"),
        mo.md(summary.round(4).to_markdown()),
    ])


if __name__ == "__main__":
    app.run()
