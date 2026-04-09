import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium", css_file="", html_head_file="")


@app.cell(hide_code=True)
def _():
    # Imports, show logo
    import marimo as mo
    import pandas as pd

    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()
    return mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # OpenTME Demo Notebook

    This notebook is an interactive demo exploring tumor microenvironment (TME) data from TCGA H&E whole slide images,
    made available to academic researchers through Aignostics' OpenTME project.

    Readouts are produced with Atlas H&E-TME, a computational pathology platform that quantifies cell types, tissue
    composition, and spatial organization via a sequential inference pipeline covering tissue quality control, tissue
    segmentation, cell detection and classification.

    The cohort presented in this notebook comprises 385 diagnostic bladder cancer slides from the TCGA BLCA project,
    with one slide selected per case. Clinical metadata were obtained from cBioPortal and molecular subtype annotations
    from Robertson et al. (Cell, 2017).
    """)


@app.cell(hide_code=True)
def _(mo):
    hf_token = mo.ui.text(kind="password", label="Your HF Token from hf.co/settings/tokens")
    mo.vstack([
        mo.md("""## Get access to the data
    OpenTME is hosted on [Hugging Face](https://huggingface.co/datasets/Aignostics/OpenTME) 🤗.  To access the dataset:

    1. Create a Hugging Face account if you don't have one — sign up for free at hf.co/join.
    2. Request access to OpenTME at huggingface.co/datasets/Aignostics/OpenTME and click "Request Access".
    3. Generate an access token at hf.co/settings/tokens and enter it in the field below to load the dataset.
        1. Go to "Repositories permissions".
        2. Select "datasets/Aignostics/OpenTME" and check boxes for read and view access.
        3. Click "create token". Enter your hugging face token in the below box to enable access to OpenTME
    """),
        hf_token,
    ])
    return (hf_token,)


@app.cell(hide_code=True)
def _(hf_token, mo, pd):
    # Download the OpenTME Bladder dataset features
    from huggingface_hub import errors, hf_hub_download

    from aignostics_tme_studio.utils import config as hf_files
    from aignostics_tme_studio.utils import utils

    token = hf_token.value or None

    try:
        path = hf_hub_download(
            repo_id=hf_files.REPO_ID,
            filename=utils.get_features_file_for_indication(hf_files.DEFAULT_INDICATION),
            repo_type="dataset",
            token=token,
            force_download=True,
        )
        df_tme = pd.read_csv(path)

        # Load metadata from this repository
        origin = mo.notebook_location() / "public"
        df_meta = pd.read_csv(origin / "metadata.csv")
        df = df_tme.merge(df_meta, left_on="TCGA_FILE_NAME", right_on="Slide name", how="inner")
        _res = df
    except errors.RepositoryNotFoundError:
        df_meta = pd.DataFrame()
        df = pd.DataFrame()
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res
    return df, df_meta, errors, hf_files, hf_hub_download, token, utils


@app.cell(hide_code=True)
def _(df_meta, mo):
    grouping_column = mo.ui.dropdown(label="Select grouping column", options=sorted(df_meta.columns))
    grouping_column
    return (grouping_column,)


@app.cell(hide_code=True)
def _(df, grouping_column, mo):
    _col = grouping_column.value
    summary = "### Cohort overview \n"
    if _col:
        if _col not in df:
            summary += f"{_col} does not exist in dataframe. No grouping was applied."
        else:
            if df[_col].isna().any():
                summary += f"Column `{_col}` does not have a value for {df[_col].isna().sum()} samples.\n"
            summary += f"Results are shown grouped by `{_col}`.\n"
            summary += f"\n{df.groupby(_col)[_col].count().to_markdown()}"
    else:
        summary += f"The cohort consists of {len(df)} samples. No grouping was applied."

    mo.vstack([mo.md(summary), df])


@app.cell(hide_code=True)
def _(errors, hf_files, hf_hub_download, token, utils):
    # Download the model output class settings and lists of available features.
    from aignostics_tme_studio.utils import column_selector

    try:
        class_settings_path = hf_hub_download(
            repo_id=hf_files.REPO_ID, filename=hf_files.CLASS_SETTINGS_FILENAME, repo_type="dataset", token=token
        )
        model_output_classes = utils.load_munch(class_settings_path)

        features_path = hf_hub_download(
            repo_id=hf_files.REPO_ID, filename=hf_files.FEAT_SETTINGS_FILENAME, repo_type="dataset", token=token
        )
        features = utils.load_statistics(features_path)
    except errors.RepositoryNotFoundError:
        features = {}
        model_output_classes = {}
    return column_selector, features, model_output_classes


@app.cell(hide_code=True)
def _(column_selector, features, mo, model_output_classes):
    _text = mo.md("""# Tissue Segmentation
    This section shows results produced by the tissue segmentation model.""")

    ts_col_selector = column_selector.FeatureColumnSelector(
        model_output_class_config=model_output_classes, statistics=features["tissue_stats"], x_variable="tissue_cls"
    )

    ts_dropdowns = ts_col_selector.render_dropdowns()
    mo.vstack([_text, ts_dropdowns])
    return ts_col_selector, ts_dropdowns


@app.cell(hide_code=True)
def _(df, features, grouping_column, ts_col_selector, ts_dropdowns):
    from aignostics_tme_studio.plotting import distributions

    _df = ts_col_selector.extract_feature_columns(df=df, **ts_dropdowns.value, grouping_column=grouping_column.value)

    _stat = next(iter([stat for stat in features["tissue_stats"] if stat.formatter == ts_dropdowns["stat"].value]))
    _title = f"{_stat.name} of a specific tissue type per slide"

    _kwargs = {
        "ytitle": str(_stat),
        "xtitle": "Tissue class",
        "title": _title,
        "subtitle": _stat.formatter,
    }

    distributions.plot_distribution(_df, grouping_column=grouping_column.value, plot_type="box", **_kwargs)
    return (distributions,)


@app.cell(hide_code=True)
def _(column_selector, features, mo, model_output_classes):
    _text = mo.md("""# Cell Detection
    This section shows nucleus statistics produced by the cell detection model.""")

    nucl_col_selector = column_selector.FeatureColumnSelector(
        model_output_class_config=model_output_classes, statistics=features["nucleus_stats"], x_variable=None
    )

    nucl_dropdowns = nucl_col_selector.render_dropdowns()
    mo.vstack([_text, nucl_dropdowns])
    return nucl_col_selector, nucl_dropdowns


@app.cell(hide_code=True)
def _(
    df,
    distributions,
    features,
    grouping_column,
    nucl_col_selector,
    nucl_dropdowns,
):
    _df = nucl_col_selector.extract_feature_columns(
        df=df, **nucl_dropdowns.value, grouping_column=grouping_column.value
    )

    _stat = next(iter([stat for stat in features["nucleus_stats"] if stat.formatter == nucl_dropdowns["stat"].value]))
    _title = f"{_stat.name} of all nuclei per slide"

    _kwargs = {
        "ytitle": str(_stat),
        "xtitle": "Tissue class",
        "title": _title,
        "subtitle": _stat.formatter,
    }

    distributions.plot_distribution(_df, plot_type="box", grouping_column=grouping_column.value, **_kwargs)


@app.cell(hide_code=True)
def _(column_selector, features, mo, model_output_classes):
    _text = mo.md("""# Cell Detection & Classification
    This section shows results produced by the cell detection and cell classification models.""")

    cc_col_selector = column_selector.CellInTissueFeatureColumnSelector(
        model_output_class_config=model_output_classes,
        statistics=features["cell_in_tissue_stats"],
        x_variable="cell_cls",
    )
    cc_dropdowns = cc_col_selector.render_dropdowns()
    mo.vstack([_text, cc_dropdowns])
    return cc_col_selector, cc_dropdowns


@app.cell(hide_code=True)
def _(
    cc_col_selector,
    cc_dropdowns,
    df,
    distributions,
    features,
    grouping_column,
):
    _df = cc_col_selector.extract_feature_columns(df=df, **cc_dropdowns.value, grouping_column=grouping_column.value)
    _formatter_str = cc_col_selector.get_column_format(cc_dropdowns.value.copy())
    _stat = next(
        iter([stat for stat in features["cell_in_tissue_stats"] if stat.formatter == cc_dropdowns["stat"].value])
    )
    _title = f"{_stat.name} of each cell type type per slide"

    _kwargs = {
        "ytitle": str(_stat),
        "xtitle": "Cell type",
        "title": _title,
        "subtitle": _formatter_str,
    }

    distributions.plot_distribution(_df, grouping_column=grouping_column.value, plot_type="box", **_kwargs)


@app.cell(hide_code=True)
def _(column_selector, features, mo, model_output_classes):
    _text = mo.md("""# Neighborhood Analysis

    This section shows results of a neighborhood analysis of the different cell classes.
    For every cell, a neighborhood statistic is computed by counting the number of cells per cell class within
    a specific neighborhood radius around the given reference cell. Neighborhood statistics can then be grouped
    by reference cell class and further filtered by roi.

    Select the type of statistics, and cell class A from the drop-downs.
    The statistic will then be plotted computed between the selected cell class A
    and all other cell classes. If a tissue type is selected, the neighborhood
    statistics are only computed for cells within that tissue type.
    """)

    nb_col_selector = column_selector.NoAnucleatedAreasFeatureColumnSelector(
        model_output_class_config=model_output_classes,
        statistics=features["neighborhood_stats"],
        x_variable="cell_cls_b",
    )
    nb_dropdowns = nb_col_selector.render_dropdowns()
    mo.vstack([_text, nb_dropdowns])
    return nb_col_selector, nb_dropdowns


@app.cell(hide_code=True)
def _(
    df,
    distributions,
    features,
    grouping_column,
    nb_col_selector,
    nb_dropdowns,
):
    _df = nb_col_selector.extract_feature_columns(df=df, **nb_dropdowns.value, grouping_column=grouping_column.value)
    _formatter_str = nb_col_selector.get_column_format(nb_dropdowns.value.copy()).upper()

    _stat = next(
        iter([stat for stat in features["neighborhood_stats"] if stat.formatter == nb_dropdowns["stat"].value])
    )
    _title = f"{_stat.name} of each cell type type per slide"

    _kwargs = {
        "ytitle": str(_stat),
        "xtitle": "Cell type",
        "title": _title,
        "subtitle": _formatter_str,
    }

    distributions.plot_distribution(_df, grouping_column=grouping_column.value, plot_type="box", **_kwargs)


@app.cell(hide_code=True)
def _(mo):
    text = mo.md("""# IDE classification
    The IDE classification of a slide is computed as follows: <br>
    1. if lymphocyte fraction in carcinoma > carcinoma threshold --> ide_classification = inflamed
    2. else: if lymphocyte fraction in stroma > stroma threshold --> ide_classification = excluded
    3. else: ide_classification = desert
    """)

    df_survival = "Disease free survival"
    oa_survival = "Overall survival"

    dropdown_metric = mo.ui.dropdown(
        options=["Density", "Percentage"],
        label="Select which metric to use to determine the presence of lymphocytes in carcinoma and stroma regions",
        value="Density",
    )

    dropdown_event = mo.ui.dropdown(
        options=[oa_survival, df_survival],
        label="Select which outcome you are interested in",
        value=oa_survival,
    )
    mo.vstack([text, dropdown_metric, dropdown_event])
    return df_survival, dropdown_event, dropdown_metric


@app.cell(hide_code=True)
def _(df, dropdown_metric, mo):
    _df = df.copy()

    if dropdown_metric.value == "Density":
        carcinoma_col = _df.CELL_DENSITY_LYMPHOCYTE_CARCINOMA
        stroma_col = _df.CELL_DENSITY_LYMPHOCYTE_STROMA
    else:
        carcinoma_col = _df.CELL_PERCENTAGE_LYMPHOCYTE_CARCINOMA
        stroma_col = _df.CELL_PERCENTAGE_LYMPHOCYTE_STROMA

    carcinoma_thresh = mo.ui.slider(
        start=carcinoma_col.min(),
        stop=carcinoma_col.max(),
        label="Select a threshold for inflamed tumor (lymphocytes in carcinoma).",
        include_input=True,
        full_width=True,
        step=1e-5,
        value=carcinoma_col.median(),
    )
    stroma_thresh = mo.ui.slider(
        start=stroma_col.min(),
        stop=stroma_col.max(),
        label="Select a threshold for excluded tumor (lymphocytes in stroma).",
        include_input=True,
        full_width=True,
        step=1e-5,
        value=stroma_col.median(),
    )

    _md = mo.md("""
    > ⚠️ Note: these features are computed for the entire stroma compartment on the slide (as opposed to only inside the
        whole tumor region (WTR). The IDE classification is meaningful only for slides in which the stroma is dominated
        by tumor-specific stroma. The user is advised to only look at excluded/desert distinction where the slides are
        suitable for such a classification.
    """)
    mo.vstack([carcinoma_thresh, stroma_thresh, _md])
    return carcinoma_thresh, stroma_thresh


@app.cell(hide_code=True)
def _(
    carcinoma_thresh,
    df,
    df_survival,
    dropdown_event,
    dropdown_metric,
    mo,
    pd,
    stroma_thresh,
):
    import numpy as np
    from lifelines import CoxPHFitter, KaplanMeierFitter
    from pandas.api.types import is_numeric_dtype

    from aignostics_tme_studio.plotting import ide_classification, kaplan_meyer

    def get_survival_df(df, disease_free: bool = False):
        # Encode survival status as binary column
        if disease_free:
            event_col = "Disease Free Status"
            time_col = "Disease Free (Months)"
        else:
            event_col = "Overall Survival Status"
            time_col = "Overall Survival (Months)"

        df = df.dropna(subset=event_col)
        df["event"] = df[event_col].str[0].astype(int)  # First character in column contains 0 or 1
        df["time"] = df[time_col].astype(float)

        return df

    def fit_kaplan_meyer(df):
        kmf = KaplanMeierFitter()
        kmf.fit(durations=df.time, event_observed=df.event, label=df.name)
        return kmf

    def fit_cox_model(df):
        dummies = pd.get_dummies(df["group"], drop_first=True)
        df = pd.concat([df, dummies], axis=1)

        cph = CoxPHFitter()
        cph.fit(df[["time", "event", *list(dummies.columns)]], duration_col="time", event_col="event")
        return cph

    def plot_kaplan_meyer_groupwise(df):
        kmfs = df.groupby("group").apply(fit_kaplan_meyer)
        kmp = kaplan_meyer.KaplanMeyerPlotter(show_censors=True)
        return kmp.render(kmfs, color_map=ide_classification.IDE_COLORS)

    def format_cox_results(cox):
        metrics = mo.hstack(
            [
                mo.vstack([mo.md("""**Cox hazard ratios:**"""), mo.md(cox.hazard_ratios_.to_markdown())]),
                mo.vstack([mo.md("""**95% CI:**"""), mo.md(np.exp(cox.confidence_intervals_).to_markdown())]),
            ],
            align="start",
        )

        footer = """*A hazard ratio of 1 implies there is no difference between the two groups.*"""
        return mo.vstack([metrics, mo.md(footer)])

    # Get DF with survival encoding and group by IDE classification
    _disease_free = dropdown_event.value == df_survival
    _df = get_survival_df(df.copy(), _disease_free)

    # ************** Computing IDE classification ********************

    ide_cls = ide_classification.IDEClassifier(
        df=_df, carcinoma_thresh=carcinoma_thresh.value, stroma_thresh=stroma_thresh.value, metric=dropdown_metric.value
    )
    _fig_ide = ide_cls.plot_ide_classification()

    # ************** Fitting survival model ********************

    _df["group"] = ide_cls.ide_classification

    # drop Nans
    _df = _df.dropna(subset=["group", "event", "time"])

    _fig_kmp = plot_kaplan_meyer_groupwise(_df)
    cox = fit_cox_model(_df)

    # ************** Formatting the result ********************

    # Print results as MD string
    _title = "## Patients split by IDE classification."

    _fig_ide.update_layout(
        autosize=False,
        width=520,
        height=400,
    )

    _fig_kmp.update_layout(
        autosize=False,
        width=520,
        height=400,
    )

    mo.hstack([
        mo.vstack([mo.md("## IDE classification"), _fig_ide]),
        mo.vstack([mo.md(_title), mo.ui.plotly(_fig_kmp), format_cox_results(cox)]),
    ])
    return (
        fit_cox_model,
        format_cox_results,
        get_survival_df,
        is_numeric_dtype,
        np,
        plot_kaplan_meyer_groupwise,
    )


@app.cell(hide_code=True)
def _(df, dropdown_event, mo):
    dropdown = mo.ui.dropdown(
        options=df.columns, label="Select a column by which to group patients", value="AJCC Pathologic Stage"
    )

    mo.vstack([
        mo.md("""# Kaplan-Meyer
    Split the patients into groups based on column values, and plot the survival curves.
    If a numerical column is selected, the patients are split by the median of the feature.
    """),
        dropdown,
        dropdown_event,
    ])
    return (dropdown,)


@app.cell(hide_code=True)
def _(df, dropdown, is_numeric_dtype, mo):
    slider = None
    _df = df
    if dropdown.value and is_numeric_dtype(_df[dropdown.value]):
        slider = mo.ui.slider(
            start=_df[dropdown.value].min(),
            stop=_df[dropdown.value].max(),
            label=f"Select a value of {dropdown.value} to split patients by.",
            include_input=True,
            step=1e-5,
            full_width=True,
            value=_df[dropdown.value].median(),
        )
    slider
    return (slider,)


@app.cell(hide_code=True)
def _(
    df,
    df_survival,
    dropdown,
    dropdown_event,
    fit_cox_model,
    format_cox_results,
    get_survival_df,
    is_numeric_dtype,
    mo,
    np,
    plot_kaplan_meyer_groupwise,
    slider,
):
    def split_by_value(df, col: str, value: float):
        return np.where(df[col] > value, f"{col} > {value:.2e}", f"{col} < {value:.2e}")

    def prep_df_for_kaplan_meyer(df, col, value: float | None = None, disease_free: bool = False):
        df = get_survival_df(df, disease_free)

        if is_numeric_dtype(df[col]):
            df["group"] = split_by_value(df, col, value)
        else:
            df["group"] = df[col]

        # Drop NaNs
        return df.dropna(subset=[col, "event", "time"])

    _disease_free = dropdown_event.value == df_survival

    if dropdown.value:
        if slider:
            _df = prep_df_for_kaplan_meyer(df.copy(), dropdown.value, slider.value, disease_free=_disease_free)
        else:
            _df = prep_df_for_kaplan_meyer(df.copy(), dropdown.value, disease_free=_disease_free)
        _fig = plot_kaplan_meyer_groupwise(_df)
        _cox = fit_cox_model(_df)

        # Print results as MD string
        _title = f"## {dropdown_event.value} for patients split by {dropdown.value}. \n"

        _cox_md = format_cox_results(_cox)

        _res = mo.vstack([mo.md(_title), _cox_md, mo.ui.plotly(_fig)])
    else:
        _res = mo.md("""Select a value from the dropdown to plot a Kaplan Meyer curve.""")
    _res


@app.cell(hide_code=True)
def _(df, df_meta, mo):
    dropdown_meta = mo.ui.dropdown(
        options=df_meta.columns,
        label="Select a metadata column by which to group patients:",
        value="AJCC Pathologic Stage",
    )
    dropdown_tme = mo.ui.dropdown(
        options=[col for col in df.columns if col not in df_meta.columns],
        label="Select a TME feature column:",
        value="CELL_PERCENTAGE_LYMPHOCYTE_STROMA",
    )

    mo.vstack([
        mo.md("""# Pairwise significance testing
    This section computes the pairwise significante between the difference in the distribution of the selected TME
    feature for each pair of values in the selected metadata feature.
    """),
        dropdown_meta,
        dropdown_tme,
    ])
    return dropdown_meta, dropdown_tme


@app.cell(hide_code=True)
def _(df, dropdown_meta, dropdown_tme, mo, pd):
    from itertools import combinations

    import plotly.express as px
    from scipy.stats import mannwhitneyu
    from statsmodels.stats.multitest import multipletests

    res = None
    if dropdown_tme.value:
        _df = df.copy()
        fig = px.box(_df, x=dropdown_meta.value, y=dropdown_tme.value)

        groups_dict = {
            name: group[dropdown_tme.value].dropna().to_numpy() for name, group in _df.groupby(dropdown_meta.value)
        }
        groups_dict = {k: v for k, v in groups_dict.items() if len(v) > 1}

        results = []
        for (name_a, a), (name_b, b) in combinations(groups_dict.items(), 2):
            _stat, p = mannwhitneyu(a, b)
            results.append({"group_a": name_a, "group_b": name_b, "p_value": p})

        results_df = pd.DataFrame(results)

        if len(results_df) > 0:
            # Correct for multiple testing
            _, p_corrected, _, _ = multipletests(results_df["p_value"], method="fdr_bh")
            results_df["p_corrected"] = p_corrected

            results_piv = results_df.pivot_table(columns="group_a", index="group_b", values="p_corrected")
            results_piv.index = ["**" + str(i) + "**" for i in results_piv.index]
            results_md = results_piv.round(4).to_markdown()
        else:
            results_md = "*No p-values to compute for only one group.*"

        res = mo.vstack([
            mo.md(f"""### Distribution of {dropdown_tme.value} for each value in {dropdown_meta.value}

    The box plot shows the distribution of the selected feature split by the selected metadata variable.
    The table shows pairwise Mann-Whitney-U values, corrected for multiple tests with Benjamini/Hochberg correction.
    """),
            mo.md(results_md),
            mo.ui.plotly(fig),
        ])
    res


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
