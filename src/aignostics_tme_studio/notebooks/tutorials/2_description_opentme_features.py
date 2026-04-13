import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Show logo
    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()


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
    # A guide through the OpenTME features 🗺️

    OpenTME contains thousands of TME features for every TCGA slide, and is fully open source.
    OpenTME was created by applying the Aignostics' Atlas H&E TME model suite to the TCGA cohort,
    with three model outputs:
    1. 🛁 **Tissue Quality Control (QC):** QC models precisely flag areas that should be excluded
    from downstream analyses.
    2. 🎈 **Cell Detection & 🎨 Classification:** Cell detection models flag individual cells
    and classify each into one of 9 different classes.
    3. 🖼️ **Tissue Segmentation:** Tissue segmentation models group relevant sections of each
    whole slide image into one of 7 different tissue regions.

    Each of these models produce a set of features which are included in OpenTME.
    Additionally, **neighbourhood analysis** 🪄 is performed, which combine outputs of multiple
    models into neighborhood features.

    For a full description of the features and how they were computed, see the [Atlas H&E-TME user manual](TODO: LINK!)
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We load the dataframe containing all OpenTME features:
    """)


@app.cell(hide_code=True)
def _(mo):
    md = mo.md("""*The following schematic shows which models produce which features. Additionally, it shows how the
    outputs of some models act as a filter for the features produced by the next model. For example, tissue features are
    only computed inside `Valid Tissue` regions produced by the QC model.*""")
    loc = mo.notebook_location()
    img = mo.image(loc / "public" / "models_schematic.svg", height="540")
    mo.vstack([md, img])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We load the dataframe containing all OpenTME features for the bladder dataset:
    """)


@app.cell
def _(hf_token):
    # Download the OpenTME bladder dataset
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config, utils

    path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=utils.get_features_file_for_indication(config.DEFAULT_INDICATION),
        repo_type="dataset",
        token=hf_token.value or None,
    )
    df = pd.read_csv(path)
    df
    return config, df, hf_hub_download, pd, utils


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # How to find features with `TME Studio` 🎨

    The dataframe contains > 4500 features! You can check out the
    [user manual](TODO add link!) for a full description of all the features.

    We now show you an example how to find some cell-level features here.
    Below, you can find a description for every available feature type in OpenTME.

    ## **Example**: Cell Densities for each cell type
    First we need to load the settings files to find out what cell classes and statistics are available.
    - `settings/model_output_classes.yaml` lists all models' output classes.
    - `settings/tme_features.yaml` lists all available stats.
    """)


@app.cell
def _(config, hf_hub_download, hf_token, utils):
    # load model output class settings
    class_settings_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=config.CLASS_SETTINGS_FILENAME,
        repo_type="dataset",
        token=hf_token.value or None,
    )
    model_output_classes = utils.load_munch(class_settings_path)

    # load available features
    features_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=config.FEAT_SETTINGS_FILENAME,
        repo_type="dataset",
        token=hf_token.value or None,
    )
    features = utils.load_statistics(features_path)
    return features, model_output_classes


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Looking at `model_output_classes['cell_cls']`, we see all available cell classes:
    """)


@app.cell
def _(model_output_classes):
    model_output_classes["cell_cls"]


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Looking at `features['cell_cls']`, we see all available cell features:
    """)


@app.cell
def _(features):
    features["cell_stats"]


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Each statistic has a `formatter` property that we can use to find the feature columns
    in the dataset. The `formatter`s for the `CELL_STATS` contain a placeholder `{cell_cls}`. We will use this below.
    """)


@app.cell
def _(features):
    stat = features["cell_stats"][3]
    stat
    return (stat,)


@app.cell(hide_code=True)
def _(features, mo):
    mo.md(f"""
    ### Finding our features
    Let's find all the {features["cell_stats"][3].name.lower()}'s for our cell classes'!

    We replace `{{cell_cls}}` by our `CELL_CLASSES` to find the feature column in the dataframe
    for each available cell type.
    """)


@app.cell
def _(df, model_output_classes, stat, utils):
    # Find all CC columns by looking over the cell classes and CC stats
    columns = []
    for _cls in model_output_classes["cell_cls"]:
        # Replace the placeholder by the cell classes
        _column = stat.formatter.format(cell_cls=_cls)

        # Columns are always uppercase.
        columns.append(utils.to_allcaps(_column))
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
    df_melt = pd.melt(df[columns])
    px.box(df_melt, x="variable", y="value")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And that's it! Below you will find instructions to be able to repeat this exercise for each feature type available
    in OpenTME.

    Find out how to add TCGA metadata in
    [tutorial 3 - including TCGA metadata](
          /?file=src/aignostics_tme_studio/notebooks/tutorials/3_including_tcga_metadata.py).
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "# Instructions for each feature type with `TME Studio` 🎨": mo.md("""

    *Below you will find working examples for each feature in OpenTME.*
    """)
    })


@app.cell(hide_code=True)
def _(df, mo):
    mo.accordion({
        "### Metadata 🧰": mo.md(
            f"""
    The first 6 columns contain metadata pertaining to each slide: <br>
    `{list(df.columns[:6])}` <br>
    The `TCGA_FILE_NAME` and `TCGA_CASE_ID` can be used to map the OpenTME features
    to metadata available in TCGA.
    """
        )
    })


@app.cell(hide_code=True)
def _(df, features, mo, model_output_classes, utils):
    _qc_cls = model_output_classes["qc_cls"]
    _stats = features["qc_stats"]
    _text = mo.md(f"""The output classes of the QC model are: `{_qc_cls}`. <br>
    The features computed for these output classes are: `{[stat.name for stat in _stats]}`.
    Additionally, there is the `ABSOLUTE_AREA` column which contains the total tissue area on the
    slide. This is the sum of the areas of each QC class, excluding the `No Tissue` class.


    You can find all QC feature columns by combining the QC classes with QC features.
    Expand the code of this cell to see how it's done!
    """)

    # Find all QC columns by looking over the QC classes and QC stats
    qc_columns = ["ABSOLUTE_AREA"]
    for _cls in _qc_cls:
        qc_columns.extend(utils.to_allcaps(_stat.formatter.format(qc_cls=_cls)) for _stat in _stats)

    # Display results
    mo.accordion({"### Tissue Quality Control (QC) 🛁": mo.vstack([_text, df[qc_columns].head()])})


@app.cell(hide_code=True)
def _(df, features, mo, model_output_classes, utils):
    _tissue_cls = model_output_classes["tissue_cls"]
    _stats = features["tissue_stats"]

    _text = mo.md(f"""The Tissue Segmentation model segments all `Valid Tissue` into one of 7 output classes:<br>
    `{_tissue_cls}`

    For each tissue class, the following features are available:<br>
    `{[s.name for s in _stats]}`
    """)

    # Find all TS columns by looking over the tissue classes and TS stats
    ts_columns = []
    for _cls in _tissue_cls:
        for _stat in _stats:
            _column = _stat.formatter.format(tissue_cls=_cls)
            ts_columns.append(utils.to_allcaps(_column))

    mo.accordion({"### Tissue Segmentation 🖼️": mo.vstack([_text, df[ts_columns].head()])})


@app.cell(hide_code=True)
def _(df, features, mo):
    _stats = features["nucleus_stats"]

    _text = mo.md(f"""The nucleus features are available in OpenTME as statistics on nucleus shapes,
    aggregated over all nuclei on the slide. The nucleus features are:
    <br>`{[s.name for s in _stats]}`.


    **Note:** Nuclei are only detected in *nucleated areas* segmented by Tissue Segmentation!
    This means that no cell nuclei are inside `Blood` or `Necrosis`.  Additionally, remember that
    Tissue Segmentation only segments `Valid Tissue` areas, so all detected nuclei must always
    lie inside `Valid Tissue` areas.
    """)

    # find all CD columns by looking over the CD stats
    cd_columns = [_stat.formatter for _stat in _stats]

    mo.accordion({"### Nucleus features 🎈": mo.vstack([_text, df[cd_columns].head()])})


@app.cell(hide_code=True)
def _(df, features, mo, model_output_classes, utils):
    _stats = features["cell_stats"]
    _cell_cls = model_output_classes["cell_cls"]

    _text = mo.md(f"""The Cell Classification model classifies each detected nucleus in one of 9 output classes:<br>
    `{_cell_cls}`

    For each cell class, the following features are available:<br>
    `{[s.name for s in _stats]}`
    """)

    # Find all CC columns by looking over the cell classes and CC stats
    cc_columns = []
    for _cls in _cell_cls:
        for _stat in _stats:
            _column = _stat.formatter.format(cell_cls=_cls)
            cc_columns.append(utils.to_allcaps(_column))

    mo.accordion({"### Cell Classification 🎨": mo.vstack([_text, df[cc_columns].head()])})


@app.cell(hide_code=True)
def _(df, features, mo, model_output_classes, utils):
    _cls = model_output_classes["tissue_cls"]
    _stats = features["cell_in_tissue_stats"]

    _text = mo.md(f"""All previous stats were computed using outputs of individual models, and aggregated over
    the entire slide. What we are really interested in, is combining model outputs.
    *What is the number lymphocytes inside carcinoma regions*? We can find an answer to this
    question by combining tissue and cell features.

    The following features are available for each cell class, inside each tissue class:
    `{[s.name for s in _stats]}`

    ***Note:** recall that Cell Detection does not find any cells in `Blood` or `Necrosis`
    regions. These features are thus also not available in `Blood` and `Necrosis`!*
    """)

    _columns = []

    # Features are not available for anucleated regions blood and necrosis. Filter them from the tissue classes.
    tissues_with_cells = [cls for cls in _cls if cls not in ["Blood", "Necrosis"]]

    for _tissue_cls in tissues_with_cells:
        for _cell_cls in model_output_classes["cell_cls"]:
            for _stat in _stats:
                _column = _stat.formatter.format(cell_cls=_cell_cls, tissue_cls=_tissue_cls)
                _columns.append(utils.to_allcaps(_column))

    mo.accordion({"### Tissue Segmentation + Cell Classification 🌈": mo.vstack([_text, df[_columns].head()])})
    return (tissues_with_cells,)


@app.cell(hide_code=True)
def _(df, features, mo, model_output_classes, tissues_with_cells, utils):
    _stats = features["neighborhood_stats"]
    _cls = model_output_classes["cell_cls"]

    _text = mo.md(f"""Now it gets interesting! What if we want to know what the number of lymphocytes is
    inside carcinoma regions, but specifically *in the neighborhood of stroma cells*?

    To answer these types of questions OpenTME contains neighborhood features, which are
    the result of neighborhood analysis. The neighborhood features are computed by considering
    each cell of type B within a certain distance from cell type A, within a certain tissue
    type (again, `Blood` and `Necrosis` don't contain any cells).

    All neighborhood features are computed for a {model_output_classes["radius"]} μm radius.
    The available features are:
    <br> `{[s.name for s in _stats]}`
    """)

    _columns = []

    for _tissue_cls in tissues_with_cells:
        for _cell_cls in _cls:
            for _cell_cls_b in _cls:
                for _stat in _stats:
                    _column = _stat.formatter.format(
                        cell_cls=_cell_cls, cell_cls_b=_cell_cls_b, tissue_cls=_tissue_cls, radius=20
                    )
                    _columns.append(utils.to_allcaps(_column))

    mo.accordion({"### Neighborhood features 🪄": mo.vstack([_text, df[_columns].head()])})


if __name__ == "__main__":
    app.run()
