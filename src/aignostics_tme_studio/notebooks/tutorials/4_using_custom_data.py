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
    # Using custom data

    You might have your own set of TME features produced by Atlas H&E-TME analysis, for example obtained via the
    [Research Access Program](https://www.aignostics.com/products/atlas-he-tme/for-academics#research-access-program).
    You can use TME Studio to explore your features the same way you would explore OpenTME.


    For some notebooks in this repository such as the Clustering example, the hugging face download code may simply be
    replaced by loading a local `.csv` file, and you're good to go. For other notebooks, such as the IDE classification
    and Kaplan-Meier analysis, you will also need to add your own survival data.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Differences between OpenTME and custom datasets
    There are two changes to look out for when using custom data:
    ### Metadata.
    **OpenTME**: Since OpenTME contains analysis results of TCGA, the first 5 columns are metadata specific to TCGA:
    `['TCGA_FILE_NAME', 'TCGA_SLIDE_UUID', 'TCGA_CASE_ID', 'TCGA_PROJECT_ID', 'INDICATION']`.

    **Custom Data:** will contain columns `SLIDE_UUID` and `SLIDE_NAME`. The `SLIDE_UUID` is an aignostics' internal
    identifier created for your slide. The `SLIDE_NAME` is the filename you provided for each slide, and can be used to
    identify your slide.

    ### Research use only header
    **OpenTME**: file names are postfixed `_RUO` to indicate research use only.

    **Custom Data:** Your data csv will have a comment header "`# For research use only`" on the first line. This must
    be skipped when loading the csv! Make sure you load the csvs with the `skiprows` argument:
    `pd.read_csv("path/to/your/file.csv", skiprows=1)`
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example
    An example file with TME features is provided in this repository at
          `src/aignostics_tme_studio/notebooks/tutorials/public/concatenated_slide_readouts.csv`, containing data for
          10 slides from the TCGA bladder cohort. The data is loaded is the cell below.
    """)


@app.cell
def _():
    # Load dataframe
    import pandas as pd

    from aignostics_tme_studio.utils import config

    df = pd.read_csv(config.EXAMPLE_CUSTOM_DATA_FILE_PATH, skiprows=1)
    df
    return df, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Using TME Studio

    The lists of available features and output classes in the OpenTME settings can be used for finding features in your
    custom data in the same way that they can be used to find features in OpenTME. See for example [tutorial 2 -
    description of all OpenTME features](
    /?file=src/aignostics_tme_studio/notebooks/tutorials/2_description_opentme_features.py). A demonstrative
    example is given below:
    """)


@app.cell
def _(df, hf_token, pd):
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config, utils

    # load model output class settings
    model_settings_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=config.MODEL_SETTINGS_FILENAME,
        repo_type="dataset",
        token=hf_token.value or None,
    )
    model_variables = utils.load_munch(model_settings_path)

    # load available features
    features_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=config.FEAT_SETTINGS_FILENAME,
        repo_type="dataset",
        token=hf_token.value or None,
    )
    features = utils.load_features(features_path)
    feat = features["cell_features"][3]

    # Find all CC columns by looking over the cell classes and CC features
    columns = []
    for _cls in model_variables["cell_cls"]:
        # Replace the placeholder by the cell classes
        _column = feat.formatter.format(cell_cls=_cls)

        # Columns are always uppercase.
        columns.append(utils.to_allcaps(_column))
    df[columns]

    import plotly.express as px

    # Plotly expects dataframes in long form
    df_melt = pd.melt(df[columns])
    px.box(df_melt, x="variable", y="value")


if __name__ == "__main__":
    app.run()
