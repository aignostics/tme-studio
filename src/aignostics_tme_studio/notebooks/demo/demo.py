import marimo

from aignostics_tme_studio.plotting import kaplan_meier

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

    Readouts are produced with Atlas H&E-TME, a computational pathology platform that quantifies cell classes, tissue
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

    _token_warning = mo.md("""
        ***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***""")

    def run_with_token(fn: callable):
        token = hf_token.value or None  # don't pass an empty string, instead pass None
        try:
            return fn(token=token), None
        except (errors.RepositoryNotFoundError, ValueError):
            return None, _token_warning

    def load_data(token: str | None):
        # Load data from Hugging Face
        path = hf_hub_download(
            repo_id=hf_files.REPO_ID,
            filename=utils.get_features_file_for_indication(hf_files.DEFAULT_INDICATION),
            repo_type="dataset",
            token=token,
        )
        df_tme = pd.read_csv(path)

        # Load metadata file from the Github repository
        df_meta = pd.read_csv(hf_files.METADATA_FILE_PATH, index_col=0)

        df = df_tme.merge(df_meta, left_on="TCGA_FILE_NAME", right_on="Slide name", how="inner")
        return df, df_meta

    _result, _warning = run_with_token(load_data)
    if _warning:
        df = pd.DataFrame()
        df_meta = pd.DataFrame()
        _warning
    else:
        df, df_meta = _result
    return df, df_meta, hf_files, hf_hub_download, run_with_token, utils


@app.cell(hide_code=True)
def _(df, df_meta, mo):
    if len(df) > 0:
        _options = sorted([col for col in df_meta.columns if "Months" not in col])
        grouping_column = mo.ui.dropdown(label="Select grouping column", options=_options)
        _res = grouping_column
    else:
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res
    return (grouping_column,)


@app.cell(hide_code=True)
def _(df, grouping_column, mo):
    if len(df) > 0:
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
                summary += f"The cohort consists of {len(df)} samples. No grouping was applied."
        _res = mo.vstack([mo.md(summary), df])
    else:
        _res = None
    _res


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Visualize model output

    For each included TCGA slide, OpenTME contains thumbnails of the H&E image and all corresponding model outputs.
    Select the slide and thumbnail type from the dropdown to view the results.
    """)


@app.cell(hide_code=True)
def _(df, hf_files, mo):
    if len(df) > 0:
        files = list(df.TCGA_FILE_NAME)
        tcga_file_dropdown = mo.ui.dropdown(options=files, value=files[0])

        thumbnail_dropdown = mo.ui.dropdown(
            options=hf_files.THUMBNAIL_FILES,
            label="Select image to display",
            value=hf_files.THUMBNAIL_FILES[0],
        )
        _res = mo.vstack([tcga_file_dropdown, thumbnail_dropdown])

    else:
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res
    return tcga_file_dropdown, thumbnail_dropdown


@app.cell(hide_code=True)
def _(
    df,
    hf_files,
    hf_hub_download,
    hf_token,
    mo,
    tcga_file_dropdown,
    thumbnail_dropdown,
):
    import base64
    from pathlib import Path

    if len(df) > 0:
        img_path = hf_hub_download(
            repo_id=hf_files.REPO_ID,
            filename=f"data/{hf_files.DEFAULT_INDICATION}/thumbnails/{tcga_file_dropdown.value}/{thumbnail_dropdown.value}",
            repo_type="dataset",
            token=hf_token.value or None,
        )
        img_b64 = base64.b64encode(Path(img_path).read_bytes()).decode()

        mime = "image/png"
        _res = mo.Html(f"<img src='data:{mime};base64,{img_b64}' style='width: auto; height: 100%' />")
    else:
        _res = None
    _res


@app.cell(hide_code=True)
def _(hf_files, hf_hub_download, run_with_token, utils):
    # Download the model output class settings and lists of available features.
    from aignostics_tme_studio.utils import column_selector

    def get_settings(token: str | None):
        class_settings_path = hf_hub_download(
            repo_id=hf_files.REPO_ID, filename=hf_files.CLASS_SETTINGS_FILENAME, repo_type="dataset", token=token
        )
        model_output_classes = utils.load_munch(class_settings_path)

        features_path = hf_hub_download(
            repo_id=hf_files.REPO_ID, filename=hf_files.FEAT_SETTINGS_FILENAME, repo_type="dataset", token=token
        )
        features = utils.load_statistics(features_path)
        return model_output_classes, features

    _result, _warning = run_with_token(get_settings)
    if _warning:
        model_output_classes = None
        features = None
        _warning
    else:
        model_output_classes, features = _result
    return column_selector, features, model_output_classes


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Cell Class Distribution Across Tissue Types
    This section shows cell classes predicted by the cell classification model, distributed across tissue types
    predicted by the tissue segmentation model.
    """)


@app.cell(hide_code=True)
def _(column_selector, df, features, model_output_classes):
    if len(df) > 0:
        cc_col_selector = column_selector.CellInTissueFeatureColumnSelector(
            model_output_class_config=model_output_classes,
            statistics=features["cell_in_tissue_stats"],
            x_variable="cell_cls",
        )
        cc_dropdowns = cc_col_selector.render_dropdowns()
        _res = cc_dropdowns
    else:
        _res = None
    _res
    return cc_col_selector, cc_dropdowns


@app.cell(hide_code=True)
def _(cc_col_selector, cc_dropdowns, df, features, grouping_column, mo):
    from aignostics_tme_studio.plotting import distributions

    if len(df) > 0:
        _df = cc_col_selector.extract_feature_columns(
            df=df, **cc_dropdowns.value, grouping_column=grouping_column.value
        )
        _formatter_str = cc_col_selector.get_column_format(cc_dropdowns.value.copy())
        _stat = next(
            iter([stat for stat in features["cell_in_tissue_stats"] if stat.formatter == cc_dropdowns["stat"].value])
        )
        _title = f"{_stat.name} of each cell class per slide"

        _kwargs = {
            "ytitle": str(_stat),
            "xtitle": "Cell class",
            "title": _title,
            "subtitle": _formatter_str,
        }

        _res = distributions.plot_distribution(_df, grouping_column=grouping_column.value, plot_type="box", **_kwargs)
    else:
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res
    return (distributions,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Neighborhood Analysis

    This section explores how different cell types are spatially organized relative to one another. For each cell,
    a neighborhood statistic is computed by counting the number of cells of each class within a defined radius. Results
    can be grouped by reference cell class and filtered by tissue type (ROI).

    Use the drop-downs to select a statistic, reference cell class, and tissue type. The plot displays the selected
    statistic between the reference class and all its neighbors - cells of any type lying within the selected distance
    radius of a reference cell - restricted to the selected tissue type.
    """)


@app.cell(hide_code=True)
def _(column_selector, df, features, model_output_classes):
    if len(df) > 0:
        nb_col_selector = column_selector.NoAnucleatedAreasFeatureColumnSelector(
            model_output_class_config=model_output_classes,
            statistics=features["neighborhood_stats"],
            x_variable="cell_cls_b",
        )
        nb_dropdowns = nb_col_selector.render_dropdowns()
        _res = nb_dropdowns
    else:
        _res = None
    _res
    return nb_col_selector, nb_dropdowns


@app.cell(hide_code=True)
def _(
    df,
    distributions,
    features,
    grouping_column,
    mo,
    nb_col_selector,
    nb_dropdowns,
):
    if len(df) > 0:
        _df = nb_col_selector.extract_feature_columns(
            df=df, **nb_dropdowns.value, grouping_column=grouping_column.value
        )
        _formatter_str = nb_col_selector.get_column_format(nb_dropdowns.value.copy()).upper()

        _stat = next(
            iter([stat for stat in features["neighborhood_stats"] if stat.formatter == nb_dropdowns["stat"].value])
        )
        _title = f"{_stat.name} of each cell class per slide"

        _kwargs = {
            "ytitle": str(_stat),
            "xtitle": "Cell class",
            "title": _title,
            "subtitle": _formatter_str,
        }

        _res = distributions.plot_distribution(_df, grouping_column=grouping_column.value, plot_type="box", **_kwargs)
    else:
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res


@app.cell(hide_code=True)
def _(mo):
    text = mo.md("""# Tumor immune phenotype classification

    The tumor immune phenotype is classified as inflamed, desert of excluded (IDE), computed as follows:
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
    if len(df) > 0:
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
        _res = mo.vstack([carcinoma_thresh, stroma_thresh, _md])
    else:
        _res = mo.md("***⚠️ Enter your Hugging Face token to be able to download the dataset and use this notebook.***")
    _res
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

    from aignostics_tme_studio.plotting import tip_classification

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

    def fit_kaplan_meier(df):
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
        kmfs = df.groupby("group").apply(fit_kaplan_meier)
        kmp = kaplan_meier.KaplanMeierPlotter(show_censors=True)
        return kmp.render(kmfs, color_map=tip_classification.IDE_COLORS)

    def format_cox_results(cox):
        metrics = mo.hstack(
            [
                mo.vstack([mo.md("""**Cox hazard ratios:**"""), mo.md(cox.hazard_ratios_.to_markdown())]),
                mo.vstack([mo.md("""**95% CI:**"""), mo.md(np.exp(cox.confidence_intervals_).to_markdown())]),
            ],
            align="start",
        )

        footer = """*A hazard ratio above 1 indicates a higher event rate in one group, while below 1 indicates
                a lower event rate.*"""
        return mo.vstack([metrics, mo.md(footer)])

    if len(df) > 0:
        # Get DF with survival encoding and group by tumor immune phenotype
        _disease_free = dropdown_event.value == df_survival
        _df = get_survival_df(df.copy(), _disease_free)

        # ************** Computing tumor immune phenotypes ********************

        ide_cls = tip_classification.TIPClassifier(
            df=_df,
            carcinoma_thresh=carcinoma_thresh.value,
            stroma_thresh=stroma_thresh.value,
            metric=dropdown_metric.value,
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
        _title = "## Kaplan-Meier Curves By Tumor Immune Phenotype"

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

        _res = mo.hstack([
            mo.vstack([mo.md("## Tumor Immune Phenotype Classification"), _fig_ide]),
            mo.vstack([mo.md(_title), mo.ui.plotly(_fig_kmp), format_cox_results(cox)]),
        ])
    else:
        _res = None
    _res


if __name__ == "__main__":
    app.run()
