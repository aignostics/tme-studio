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
def _():
    import marimo as mo
    # Get Hugging Face token

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
def _(hf_token):
    # Load dataframe
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config

    # Download the OpenTME bladder dataset
    path = hf_hub_download(
        repo_id=config.REPO_ID, filename=config.FEATURES_FILENAME, repo_type="dataset", token=hf_token.value or None
    )
    df = pd.read_csv(path)
    return df, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Where to find TCGA metadata 🗄️
    Clinical and pathological metadata can be obtained from the [NCI GDC Data Portal](https://portal.gdc.cancer.gov/)
    (TSV download or API) or [cBioPortal](https://www.cbioportal.org/) (tabular downloads). For harmonized survival
    endpoints (OS, DSS, PFI, DFI) across all TCGA cohorts, see the
    [Pan-Cancer Clinical Data Resource (Liu et al., 2018)](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0).
    Metadata can be linked to our outputs via the TCGA barcode (first 12 characters, e.g., TCGA-A2-A0T2), included in
    our `tme_features_RUO.csv` files.
    """)


@app.cell(hide_code=True)
def _(df, mo):
    tcga_id_columns = ["TCGA_FILE_NAME", "TCGA_SLIDE_ID", "TCGA_CASE_ID"]

    _text = mo.md(f""" # TCGA case and file identifiers 🔬

    The OpenTME data contains three columns by which we can identify to which patient/case in TCGA they belong:<br>
    `{tcga_id_columns}`.
    """)

    mo.vstack([_text, df[tcga_id_columns].head()])
    return (tcga_id_columns,)


@app.cell(hide_code=True)
def _(mo):
    origin = mo.notebook_location() / "public"

    mo.vstack([
        mo.md("The TCGA file name contains a lot of information to help us identify the sample:"),
        mo.image(src=origin / "tcga_name_structure.png", width=600),
    ])
    return (origin,)


@app.cell(hide_code=True)
def _(df, mo, tcga_id_columns):
    row = df[tcga_id_columns].iloc[0]

    _text = mo.md(f"""Looking at the first row of our dataframe as an example, we can see how the TCGA identifiers
    relate:

    The `TCGA_CASE_ID` equals the first 12 characters in the `TCGA_FILE_NAME`:<br>
    {row.TCGA_CASE_ID} --> **{row.TCGA_FILE_NAME[:12]}**{row.TCGA_FILE_NAME[12:]}

    The `TCGA_SLIDE_ID` equals the ID in the `TCGA_FILE_NAME`: <br>
    {row.TCGA_FILE_NAME} --> {row.TCGA_FILE_NAME.split(".")[0]}**{row.TCGA_FILE_NAME.split(".")[1]}**
    """)

    mo.vstack([
        _text,
        row,
    ])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Our example metadata contains the TCGA slide name in a column `Slide name`. We can merge the dataframe on this
    column to add the metadata to our OpenTME features.
    """)


@app.cell
def _(df, origin, pd):
    df_meta = pd.read_csv(origin / "metadata.csv")

    df_all = df.merge(df_meta, left_on="TCGA_FILE_NAME", right_on="Slide name")
    df_all.head()
    return df_all, df_meta


@app.cell(hide_code=True)
def _(df, df_meta, mo):
    md = mo.md(
        """Now we can use the metadata for further analysis. Let's simply plot some datapoints and color them by a
        metadata variable."""
    )
    dropdown_x = mo.ui.dropdown(options=df.columns[6:], value=df.columns[6], label="Pick a variable for the x-axis:")
    dropdown_y = mo.ui.dropdown(options=df.columns[6:], value=df.columns[7], label="Pick a variable for the y-axis:")
    dropdown_c = mo.ui.dropdown(
        options=df_meta.columns, value="Overall Survival Status", label="Pick a TCGA metadata variable:"
    )

    mo.vstack([md, dropdown_x, dropdown_y, dropdown_c])
    return dropdown_c, dropdown_x, dropdown_y


@app.cell
def _(df_all, dropdown_c, dropdown_x, dropdown_y, styling_utils):
    import plotly.express as px

    # Create color map
    color_map = styling_utils.get_color_map(df_all[dropdown_c.value].unique())

    px.scatter(
        df_all,
        x=df_all[dropdown_x.value],
        y=df_all[dropdown_y.value],
        color=df_all[dropdown_c.value],
        color_discrete_map=color_map,
    )


if __name__ == "__main__":
    app.run()
