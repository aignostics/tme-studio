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
    df = pd.read_csv(path)
    return config, df, hf_hub_download, utils


@app.cell(hide_code=True)
def _(config, mo):
    mo.md(f"""
    # Outlier detection 🕵️‍♀️
    In this tutorial, we show you how to detect some outliers from QC features, and how to use the **model output
    thumbnails** to diagnose the problem behind these outlier slides.


    ## Loading the data
    We load the `RELATIVE_AREA_<qc_cls>` for each QC class in the `{config.CLASS_SETTINGS_FILENAME}` file.
    """)


@app.cell
def _(config, df, hf_hub_download, utils):
    # Load model output class settings
    class_settings_path = hf_hub_download(
        repo_id=config.REPO_ID, filename=config.CLASS_SETTINGS_FILENAME, repo_type="dataset"
    )
    model_output_classes = utils.load_munch(class_settings_path)

    # Find all QC columns by looking over the QC classes and QC stats
    qc_columns = [utils.to_allcaps(f"RELATIVE_AREA_{_cls}") for _cls in model_output_classes["qc_cls"]]

    df_qc = df[qc_columns]
    df_qc
    return (df_qc,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pre-processing

    The magnitude of the QC features can vary between very large numbers (`RELATIVE_AREA_VALID_TISSUE`) and small
    numbers (`RELATIVE_AREA_MARKER`), so standardization of the features is necessary.

    Additionally, we replace any `NaN` values with zero to allow sklearn estimators to process empty features.
    """)


@app.cell
def _(df_qc):
    from sklearn import preprocessing

    scaler = preprocessing.StandardScaler()
    qc_normalized = scaler.fit_transform(df_qc.fillna(0))
    return (qc_normalized,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Outlier detection
    To detect outliers, we use an [IsolationForest](
    https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.
    html#sklearn.ensemble.IsolationForest) and set the dataset contamination to 0.01, meaning we expect 1% of our data
    to be outliers.
    """)


@app.cell
def _(qc_normalized):
    from sklearn import ensemble

    estimator = ensemble.IsolationForest(contamination=0.01).fit(qc_normalized)
    y = estimator.predict(qc_normalized)
    return (y,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Visualization
    ## Principal Component Analysis (PCA)
    We visualize the outliers by performing a dimensional reduction of the data via PCA. We plot the first two
    components, and color the datapoint by whether they are in-distribution or outliers.
    """)


@app.cell
def _(qc_normalized, styling_utils, y):
    import numpy as np
    import plotly.express as px
    from sklearn import decomposition

    # Run PCA with 2 components
    pca = decomposition.PCA().fit_transform(qc_normalized)

    labels = np.where(y == 1, "in distribution", "outlier")
    # Create color map for the labels
    color_map = styling_utils.get_color_map(np.unique(labels.astype(str)))

    # Plot as a scatter plot
    px.scatter(x=pca[:, 0], y=pca[:, 1], color=labels.astype(str), color_discrete_map=color_map)
    return (labels,)


@app.cell
def _(df, labels, mo):
    md = mo.md(f"""## QC segmentation
    To find out why these slides are marked as outliers, let's have a look at the QC segmentation maps our outliers.
    Select a slide from the dropdown for visual inspection. The average relative area for `Valid tissue` in these slides
    is {round(df["RELATIVE_AREA_VALID_TISSUE"].mean())}%. We expect our outliers to have large invalid tissue regions.
    """)  # noqa: S608
    outliers = list(df[labels == "outlier"].TCGA_FILE_NAME)
    dropdown = mo.ui.dropdown(options=outliers, value=outliers[0])

    mo.vstack([md, dropdown])
    return (dropdown,)


@app.cell
def _(config, dropdown, hf_hub_download, hf_token, mo):
    img_path = hf_hub_download(
        repo_id=config.REPO_ID,
        filename=f"data/{config.DEFAULT_INDICATION}/thumbnails/{dropdown.value}/tissue_qc.png",
        repo_type="dataset",
        token=hf_token.value or None,
    )

    mo.image(img_path, style={"height": "100%", "width": "auto"})


if __name__ == "__main__":
    app.run()
