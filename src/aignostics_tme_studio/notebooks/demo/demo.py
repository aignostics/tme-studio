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
    return mo, pd, styling_utils


@app.cell(hide_code=True)
def _(styling_utils):
    styling_utils.load_css()


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
        # Load data from Hugging Face
        path = hf_hub_download(
            repo_id=hf_files.REPO_ID,
            filename=utils.get_features_file_for_indication(hf_files.DEFAULT_INDICATION),
            repo_type="dataset",
            token=token,
            force_download=True,
        )
        df_tme = pd.read_csv(path)

        # Load metadata file from the Github repository
        df_meta = pd.read_csv(hf_files.METADATA_FILE_PATH, index_col=0)

        df = df_tme.merge(df_meta, left_on="TCGA_FILE_NAME", right_on="Slide name", how="inner")
        _res = None
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
    _text = mo.md("""# Cell Class Distribution Across Tissue Types
    This section shows cell classes predicted by the cell classification model, distributed across tissue types
    predicted by the tissue segmentation model.
    """)

    cc_col_selector = column_selector.CellInTissueFeatureColumnSelector(
        model_output_class_config=model_output_classes,
        statistics=features["cell_in_tissue_stats"],
        x_variable="cell_cls",
    )
    cc_dropdowns = cc_col_selector.render_dropdowns()
    mo.vstack([_text, cc_dropdowns])
    return cc_col_selector, cc_dropdowns


@app.cell(hide_code=True)
def _(cc_col_selector, cc_dropdowns, df, features, grouping_column):
    from aignostics_tme_studio.plotting import distributions

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
    return (distributions,)


@app.cell(hide_code=True)
def _(column_selector, features, mo, model_output_classes):
    _text = mo.md("""# Neighborhood Analysis

    This section explores how different cell types are spatially organized relative to one another. For each cell,
    a neighborhood statistic is computed by counting the number of cells of each class within a defined radius. Results
    can be grouped by reference cell class and filtered by tissue type (ROI).

    Use the drop-downs to select a statistic type and a reference cell class. The plot will display the selected
    statistic between the reference class and all other cell classes. If a tissue type is selected, only cells within
    that tissue type are included in the analysis.

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
    text = mo.md("""# Tumor immune phenotype classification
    The tumor immune phenotype classification of a slide is computed as follows:<br>
    ```
    if lymphocyte fraction in carcinoma > carcinoma threshold:
        classification = inflamed

    elif lymphocyte fraction in stroma > stroma threshold:
        classification = excluded

    else:
        classification = desert
    ```
    """)

    df_survival = "Disease free survival"
    oa_survival = "Overall survival"

    dropdown_metric = mo.ui.dropdown(
        options=["Density", "Percentage"],
        label="Select which metric to use to determine presence of lymphocytes in carcinoma and stroma regions.",
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
    > ⚠️ Note: These features are computed across the entire stroma compartment of the slide, not exclusively for
        tumor-associated stroma within the whole tumor region (WTR). Consequently, the tumor immune phenotype
        classification — particularly the distinction between excluded and desert phenotypes — should be interpreted
        with caution on slides with substantial amounts of tumor-independent stroma.
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

    from aignostics_tme_studio.plotting import kaplan_meyer, tip_classification

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
        return kmp.render(kmfs, color_map=tip_classification.IDE_COLORS)

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

    # Get DF with survival encoding and group by tumor immune phenotype
    _disease_free = dropdown_event.value == df_survival
    _df = get_survival_df(df.copy(), _disease_free)

    # ************** Computing tumor immune phenotypes ********************

    ide_cls = tip_classification.TIPClassifier(
        df=_df, carcinoma_thresh=carcinoma_thresh.value, stroma_thresh=stroma_thresh.value, metric=dropdown_metric.value
    )
    _fig_ide = ide_cls.plot_tip_classification()

    # ************** Fitting survival model ********************

    _df["group"] = ide_cls.phenotype_classification

    # drop Nans
    _df = _df.dropna(subset=["group", "event", "time"])

    _fig_kmp = plot_kaplan_meyer_groupwise(_df)
    cox = fit_cox_model(_df)

    # ************** Formatting the result ********************

    # Print results as MD string
    _title = "## Kaplan-Meier Survival Curves by tumor immune phenotype Class"

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
        mo.vstack([mo.md("## Tumor immune phenotype classification"), _fig_ide]),
        mo.vstack([mo.md(_title), mo.ui.plotly(_fig_kmp), format_cox_results(cox)]),
    ])


if __name__ == "__main__":
    app.run()
