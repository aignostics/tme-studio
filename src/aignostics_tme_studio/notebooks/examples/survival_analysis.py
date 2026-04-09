import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Show logo
    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()


@app.cell(hide_code=True)
def _():
    # Get Hugging Face token
    import marimo as mo

    _md = mo.md("""Enter your hugging face token in the below box to enable access to OpenTME.""")

    _acc = mo.accordion({
        "Click here for instructions to create a Hugging Face token": """Create an access token by going to [hf.co/settings/tokens](https://hf.co/settings/tokens)
        1. Go to "Repositories permissions".
        2. Select "datasets/Aignostics/OpenTME" and check boxes for read and view access.
        3. Click "create token". Enter your hugging face token in the below box to enable access to OpenTME.
                         """
    })
    hf_token = mo.ui.text(kind="password", label="Your HF Token from hf.co/settings/tokens")
    mo.vstack([_md, _acc, hf_token])
    return hf_token, mo


@app.cell(hide_code=True)
def _(hf_token, mo):
    # Load dataframe with metadata
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config, utils

    # Download the OpenTME bladder dataset
    path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=utils.get_features_file_for_indication(config.DEFAULT_INDICATION),
        repo_type="dataset",
        token=hf_token.value or None,
    )
    df_tme = pd.read_csv(path)

    # Load survival data
    origin = mo.notebook_location() / "public"
    df_meta = pd.read_csv(origin / "metadata.csv")

    # Store relevant columns (dropping IMAGE_RESOLUTION etc.)
    tme_feat = df_tme.columns[6:]

    df = df_tme.merge(df_meta, left_on="TCGA_FILE_NAME", right_on="Slide name", how="inner")
    return df, pd, tme_feat


@app.cell(hide_code=True)
def _(df, mo):
    survival_columns = [
        "Disease Free (Months)",
        "Disease Free Status",
        "Overall Survival (Months)",
        "Overall Survival Status",
    ]

    mo.vstack([
        mo.md(f"""# Survival analysis 📈

    This notebook shows how one can find features in OpenTME that correlate with survival,
    and how to plot Kaplan-Meyer curves stratified by such a feature.


    For the purpose of this example we need survival data. This is not included in OpenTME, but may be extracted from
    TCGA directly.
    We extracted survival data for a small subset of TCGA slides and add this to the dataframe.

    The survival data can be found in columns `{survival_columns}`
    """),
        df[survival_columns],
    ])


@app.cell(hide_code=True)
def _(mo):
    overall = "Overall Survival"
    disease_free = "Disease Free Survival"

    _text = mo.md("""Select which survival type you are interested in from the dropdown""")
    dropdown = mo.ui.dropdown(options=[overall, disease_free], value=overall)
    mo.vstack([_text, dropdown])
    return dropdown, overall


@app.cell(hide_code=True)
def _(df, dropdown, mo, overall):
    # Pick event and time columns based on dropdown selection
    event_col = "Overall Survival Status" if dropdown.value == overall else "Disease Free Status"
    time_col = "Overall Survival (Months)" if dropdown.value == overall else "Disease Free (Months)"

    # Encode survival status as binary column
    df_survival = df.copy().dropna(subset=[event_col, time_col])
    df_survival[event_col] = df_survival[event_col].str[0]  # Extract first char, 0 or 1 indicating survival status

    mo.vstack([
        mo.md(
            "We join the survival data with our OpenTME features,"
            " and group by 'event' to see how many slides we have for the survival categories."
        ),
        mo.md(df_survival.groupby(event_col).TCGA_FILE_NAME.count().to_markdown()),
    ])
    return df_survival, event_col, time_col


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Get most correlated feature

    We use the column `Overall Survival Status` and find the feature that correlates most strongly with it.
    """)


@app.cell
def _(df_survival, event_col, mo, pd, tme_feat):
    import numpy as np
    from scipy.stats import pointbiserialr

    correlations = np.zeros((len(tme_feat),))

    for i, _feat_col in enumerate(tme_feat):
        # Only select rows that have a value for this feature
        mask = ~df_survival[_feat_col].isna()

        # Convert binary survival status to boolean
        # This has to go via int conversion, as a string "0" also gives boolean "True"
        e = df_survival[event_col][mask].astype(int).astype(bool)
        f = df_survival[_feat_col][mask]

        # Skip features that N/A for many cases, as well as non-numeric features
        if len(e) < 100 or not pd.api.types.is_numeric_dtype(f) or len(e.unique()) == 1:
            continue

        # Compute correlation and store
        correlation, _ = pointbiserialr(x=e, y=f.astype(float))
        correlations[i] = correlation

    # Get most correlated features
    feat = tme_feat[np.abs(correlations).argmax()]
    mo.md(f"""Most correlated feature with survival: `{feat}`""")
    return feat, np


@app.cell
def _(df, event_col, feat, mo):
    import plotly.express as px

    fig = px.box(df, x=event_col, y=feat)

    mo.vstack([mo.md("""## Distribution of most correlated feature vs. survival status"""), mo.ui.plotly(fig)])


@app.cell(hide_code=True)
def _(df, feat, mo):
    _text = mo.md(f"""## Kaplan-Meyer
    Now that we've found the feature that correlates most strongly with survival,
    let's try to see how it affects the Kaplan-Meyer analysis.

    We split the patients into two groups, having a value for `{feat}` either above of below
    the value of the slider. We then plot the Kaplan-Meyer curves for both groups.
    """)
    slider = mo.ui.slider(
        start=df[feat].min(),
        stop=df[feat].max(),
        label=f"Select a value of `{feat}` to split patients by.",
        include_input=True,
        step=1e-5,
        full_width=True,
        value=df[feat].median(),
    )
    mo.vstack([_text, slider])
    return (slider,)


@app.cell
def _(df_survival, event_col, feat, mo, np, slider, time_col):
    from lifelines import KaplanMeierFitter

    from aignostics_tme_studio.plotting import kaplan_meyer

    def fit_kaplan_meyer(df):
        kmf = KaplanMeierFitter()
        kmf.fit(durations=df[time_col].astype(float), event_observed=df[event_col].astype(bool), label=df.name)
        return kmf

    def plot_kaplan_meyer_groupwise(df):
        kmfs = df.groupby("group").apply(fit_kaplan_meyer)
        kmp = kaplan_meyer.KaplanMeyerPlotter(show_censors=True)
        return kmp.render(kmfs)

    def split_by_value(df, col: str, value: float):
        return np.where(df[col] > value, f"{col} > {value:.2e}", f"{col} < {value:.2e}")

    # Split patients into two groups, having feature above or below the value given by the slider
    df_survival["group"] = split_by_value(df_survival, feat, slider.value)

    # Fit Kaplan-Meyer estimator and plot for each group
    _fig = plot_kaplan_meyer_groupwise(df_survival.dropna(subset=["group", event_col, time_col]))

    # Display results
    _title = f"Overall survival for patients split by `{feat}` larger or smaller than {slider.value:.2e}. \n"
    mo.vstack([mo.md(_title), mo.ui.plotly(_fig)])


if __name__ == "__main__":
    app.run()
