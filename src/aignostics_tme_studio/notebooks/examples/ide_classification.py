import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Show logo
    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()
    return


@app.cell(hide_code=True)
def _():
    # Get Hugging Face token
    import marimo as mo

    _md = mo.md("""Enter your hugging face token in the below box to enable access to OpenTME.""")

    _acc = mo.accordion({"Click here for instructions to create a Hugging Face token": """Create an access token by going to [hf.co/settings/tokens](https://hf.co/settings/tokens)
        1. Go to "Repositories permissions".
        2. Select "datasets/Aignostics/OpenTME" and check boxes for read and view access.
        3. Click "create token". Enter your hugging face token in the below box to enable access to OpenTME.
                         """})
    hf_token = mo.ui.text(kind="password", label="Your HF Token from hf.co/settings/tokens")
    mo.vstack([_md, _acc, hf_token])
    return hf_token, mo


@app.cell(hide_code=True)
def _(hf_token):
    # Load dataframe
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config

    # Download the OpenTME bladder dataset
    path = hf_hub_download(repo_id=config.REPO_ID, filename=config.FEATURES_FILENAME, repo_type="dataset", token=hf_token.value or None)
    df = pd.read_csv(path)
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # IDE classification 🫚

    IDE stands for inflamed/desert/excluded, and is a method for classifying slides based on their
    inflammation status.

    We can use the OpenTME features `CELL_DENSITY_LYMPHOCYTE_CARCINOMA` and
    `CELL_DENSITY_LYMPHOCYTE_STROMA` to classify our slides into the three groups.
    The IDE classification of a slide is computed as follows:

    ```
    if CELL_DENSITY_LYMPHOCYTE_CARCINOMA > threshold_carcinoma:
        ide_classification = inflamed

    elif CELL_DENSITY_LYMPHOCYTE_STROMA > threshold_stroma:
        ide_classification = excluded

    else:
        ide_classification = desert
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _md = mo.md(
        """First choose which metric to use to determine presence of lymphocytes in carcinoma and stroma regions."""
    )
    dropdown = mo.ui.dropdown(options=["Density", "Percentage"], label="metric", value="Density")
    mo.vstack([_md, dropdown])
    return (dropdown,)


@app.cell(hide_code=True)
def _(df, dropdown, mo):
    if dropdown.value == "Density":
        carcinoma_col = df.CELL_DENSITY_LYMPHOCYTE_CARCINOMA
        stroma_col = df.CELL_DENSITY_LYMPHOCYTE_STROMA
    else:
        carcinoma_col = df.CELL_PERCENTAGE_LYMPHOCYTE_CARCINOMA
        stroma_col = df.CELL_PERCENTAGE_LYMPHOCYTE_STROMA

    carcinoma_thresh = mo.ui.slider(
        start=carcinoma_col.min(),
        stop=carcinoma_col.max(),
        label="Select threshold for inflamed tumor (lymphocytes in carcinoma).",
        include_input=True,
        full_width=True,
        step=1e-5,
        value=carcinoma_col.median(),
    )
    stroma_thresh = mo.ui.slider(
        start=stroma_col.min(),
        stop=stroma_col.max(),
        label="Select threshold for excluded tumor (lymphocytes in stroma).",
        include_input=True,
        full_width=True,
        step=1e-5,
        value=stroma_col.median(),
    )
    _md_1 = mo.md("""Use the sliders below to select a threshold for the lymphocyte densities in carcinoma and stroma,
    and see how this classifies your slide into the IDE groups.""")
    _md_2 = mo.md("""> ⚠️ Note: these features are computed for the entire stroma compartment on the slide (as opposed to
        only inside the whole tumor region (WTR). The IDE classification is meaningful only for slides in which the
        stroma is dominated by tumor-specific stroma. The user is advised to only look at the distinction between
        excluded and desert where the slides are suitable for such a classification.""")
    mo.vstack([_md_1, carcinoma_thresh, stroma_thresh, _md_2])
    return carcinoma_thresh, stroma_thresh


@app.cell
def _(carcinoma_thresh, df, dropdown, mo, stroma_thresh):
    from aignostics_tme_studio.plotting import ide_classification

    ide_cls = ide_classification.IDEClassifier(
        df=df, carcinoma_thresh=carcinoma_thresh.value, stroma_thresh=stroma_thresh.value, metric=dropdown.value
    )

    fig = ide_cls.plot_ide_classification()
    tab = ide_cls.get_distribution_table()

    tab = tab.style.format({"count": "{:,.2%}".format}).hide()
    mo.hstack([fig, tab], align="start", widths=[0.7, 0.3])
    return


if __name__ == "__main__":
    app.run()
