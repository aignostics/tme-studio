import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Imports, show logo
    import marimo as mo

    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()
    return (mo,)


@app.cell(hide_code=True)
def _(styling_utils):
    styling_utils.load_css()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Welcome! 🌈

    Welcome to the **getting started** tutorial on the **OpenTME** dataset.


    ### What is OpenTME?
    OpenTME is the output of comprehensive tumor-microenvironment analysis of the full TCGA dataset using
    [Atlas H&E-TME](https://www.aignostics.com/products/he-tme-profiling-product). You can find the dataset on
    [Hugging Face](https://huggingface.co/datasets/Aignostics/OpenTME) 🤗.


    This tutorial is part of the [`TME Studio 🎨`](https://github.com/aignostics/tme-studio)
    repository, which provides a set of tutorials and examples to get you familiar with the OpenTME
    dataset, and a glimpse of the types of analyses that are possible with it.


    *These tutorials are marimo notebooks.
    Not familiar with Marimo? Get started with [this tutorial](https://molab.marimo.io/notebooks/nb_TWVGCgZZK4L8zj5ziUBNVL)*
    """)


@app.cell(hide_code=True)
def _(mo):
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
    return (hf_token,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # What's inside OpenTME?

    OpenTME contains data for 5 indications: Bladder, Breast, Liver, Colorectal, and Lung cancer. ***TODO*** For each
    indication in TCGA, OpenTME contains the following (see directory tree below):
    * `tme_features_RUO.csv`: contains the OpenTME features.
    * A folder `thumbnails` containing, for each WSI, a folder `<TCGA_FILENAME>` containing a set of thumbnails,
          one being the WSI itself, and three visualizing the Aignostics' Atlas H&E TME model outputs,
          allowing you to verify the model predictions:
      * `wsi.png`: The TCGA WSI at 42 mpp.
      * `tissue_qc.png`: A plot showing the output of the tissue quality control model.
      * `tissue_segmentation.png`: A plot showing the output of the tissue segmentation model.
      * `cell_classification.png`: A plot of the cell classification model output, showing cell centers colored
          by cell type.

    OpenTME additionally contains a `settings/` folder, containing
    * The available model output classes in `model_output_classes.yaml`
    *  The available statistics in `tme_features.yaml`
    """)


@app.cell(hide_code=True)
def _(mo):
    _dir = mo.md("""
    ```text
    OpenTME/
    |-- data/
        |-- indication A/
            |-- tme_features_RUO.csv
            |-- thumbnails/
                |-- TCGA-XX.../
                    |-- wsi.png
                    |-- tissue_qc.png
                    |-- tissue_segmentation.png
                    |-- cell_classification.png
                |-- TCGA-YY.../
                |-- TCGA-ZZ.../
                |-- ...
        |-- indication B/
            |-- tme_features_RUO.csv
            |-- thumbnails/
        |-- indication C/
        |-- ...
    |-- settings/
        |-- model_output_classes.yaml
        |-- tme_features.yaml
    ```
    """)
    mo.accordion({"View directory structure of OpenTME": _dir})


@app.cell(hide_code=True)
def _(mo):
    from aignostics_tme_studio.utils import config

    _md = mo.md(f"""# Indications
    There are {len(config.INDICATIONS)} indications available in OpenTME. Select one from
    the dropdown to view some details from this indication below.
    """)  # noqa: S608

    indication_selector = mo.ui.dropdown(
        options=list(config.INDICATIONS),
        label="Select indication",
        value=config.DEFAULT_INDICATION,
    )
    mo.vstack([_md, indication_selector])
    return config, indication_selector


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `tme_features_RUO.csv`

    Each row in the `tme_features_RUO.csv` files relates to one slide. Let's load the features for the selected
    indication and view what's inside...
    """)


@app.cell
def _(config, hf_token, indication_selector):
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import utils

    path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=utils.get_features_file_for_indication(indication_selector.value),
        repo_type="dataset",
        token=hf_token.value or None,
    )
    df = pd.read_csv(path)
    df
    return df, hf_hub_download, pd, utils


@app.cell(hide_code=True)
def _(df, mo):
    _md = mo.md(f"""
    # Thumbnails

    The thumbnails for each slide and its model outputs can be downloaded from the path
    `{{indication}}/thumbnails/{{TCGA_SLIDE_NAME}}/{{image name}}.png`

    Let's have a look at the thumbnails for the first slide in the dataframe, `{df.iloc[0].TCGA_FILE_NAME}`.
    """)
    dropdown = mo.ui.dropdown(
        options=["wsi", "tissue_qc", "tissue_segmentation", "cell_classification"],
        label="Select image to display",
        value="wsi",
    )

    mo.vstack([_md, dropdown])
    return (dropdown,)


@app.cell
def _(
    config,
    df,
    dropdown,
    hf_hub_download,
    hf_token,
    indication_selector,
    mo,
):
    img_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=f"data/{indication_selector.value}/thumbnails/{df.iloc[0].TCGA_FILE_NAME}/{dropdown.value}.png",
        repo_type="dataset",
        token=hf_token.value or None,
    )

    mo.image(img_path, style={"width": "auto", "height": "100%"})


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Settings

    The `settings/` folder contains two files.

    - `settings/model_output_classes.yaml` lists the output classes of the individual Atlas H&E-TME models.

    - `settings/tme_features.yaml` lists all available cell statistics.

    You will learn how to use these files in
    [tutorial 2 - description of all OpenTME features](
          /?file=src/aignostics_tme_studio/notebooks/tutorials/2_description_opentme_features.py).
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's load `model_output_classes.yaml` to find all available tissue classes:
    """)


@app.cell
def _(config, hf_hub_download, hf_token, utils):
    # Load model output class settings
    class_settings_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=config.CLASS_SETTINGS_FILENAME,
        repo_type="dataset",
        token=hf_token.value or None,
    )
    model_output_classes = utils.load_munch(class_settings_path)
    model_output_classes["tissue_cls"]
    return (model_output_classes,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Example: Tissue areas
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's find all the tissue areas! The tissue areas can be found in columns `RELATIVE_AREA_{tissue_cls}`

    We replace the placeholder `{tissue_cls}` by the values in `model_output_classes["tissue_cls"]` (the list of
    available tissue classed in the OpenTME dataset we loaded in the cell above).
    With this, we can find the respective feature column in the dataframe for each available tissue type.
    """)


@app.cell
def _(df, model_output_classes, utils):
    # Find all relative tissue area columns by looking over the tissue classes
    columns = []
    for _cls in model_output_classes["tissue_cls"]:
        # Replace the placeholder by the tissue classes
        column = f"RELATIVE_AREA_{utils.to_allcaps(_cls)}"

        # Columns are always uppercase
        columns.append(column)
    df[columns]
    return (columns,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Let's plot our features!

    Now we have found our feature columns, we can plot the distribution over all slides in the dataset.
    """)


@app.cell
def _(columns, df, pd):
    import plotly.express as px

    # Plotly expects dataframes in long form
    df_melt = pd.melt(df[columns], var_name="Tissue Class", value_name="Relative Area")
    px.box(df_melt, x="Tissue Class", y="Relative Area")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And that's it! You find details on how to find columns for each feature type in
    [tutorial 2 - description of all OpenTME features](
          /?file=src/aignostics_tme_studio/notebooks/tutorials/2_description_opentme_features.py)
    """)


if __name__ == "__main__":
    app.run()
