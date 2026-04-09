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
    # Load dataframe
    import pandas as pd
    from huggingface_hub import hf_hub_download

    from aignostics_tme_studio.utils import config

    # Download the OpenTME bladder dataset
    path = hf_hub_download(
        repo_id=config.REPO_ID, filename=config.FEATURES_FILENAME, repo_type="dataset", token=hf_token.value or None
    )
    df = pd.read_csv(path)
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Clustering

    This tutorial shows how you can run a clustering algorithm on the features in OpenTME.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pre-processing the dataframe

    We start by cleaning up the dataframe for clustering purposes.

    ### Drop  metadata columns
    The first 6 columns contain metadata. We drop them to create a dataframe with only TME features.

    Additionally, the column `CELL_CLASSES` contains string values, namely a list of all cell types found on the slide.
    We drop this as well.
    """)


@app.cell
def _(df):
    # Drop metadata
    tme_feat_cols = df.columns[6:]
    # Drop cell_classes
    tme_feat_cols = [col for col in tme_feat_cols if col != "CELL_CLASSES"]
    df[tme_feat_cols]
    return (tme_feat_cols,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Drop absolute values
    Some features in the dataframe contain absolute values, such as `ABSOLUTE_AREA_BLOOD` or `REGION_COUNT_STROMA`.
    Since these features simply depend on the size of the slide, they are not meaningful for us in this context. We
    drop them as well.
    """)


@app.cell
def _(df, tme_feat_cols):
    features_to_drop = [
        "ABSOLUTE_AREA",  # Absolute value, total area of the tissue on the slide
        "REGION_COUNT",  # Absolute value, total number of tissue regions
        "CELL_N_TOTAL",  # Absolute value, total number of cells
        "CELL_COUNT",  # Absolute value, total number of cells of a certain type
    ]

    meaningful_tme_feat_cols = tme_feat_cols

    for _feat in features_to_drop:
        meaningful_tme_feat_cols = [col for col in meaningful_tme_feat_cols if _feat not in col]
    df_feat = df[meaningful_tme_feat_cols]
    return (df_feat,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Dealing with `NaN`s
    K-means clustering cannot handle `NaN` values in the dataframe. OpenTME contains many `NaN` values. They arise when
    certain properties cannot be computed, for example the number of cells inside `Vessel` regions, when there are no
    `Vessel` regions on the slide. Or: the percentage of cells around `macrophages`, when there are no `macrophages` on
    the slide.
    For our purpose, we simply set all `NaN` values to zero.
    """)


@app.cell
def _(df_feat):
    df_feat_no_nans = df_feat.fillna(0)
    return (df_feat_no_nans,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Clustering the dataframe
    """)


@app.cell(hide_code=True)
def _(mo):
    dropdown = mo.ui.dropdown(options=range(2, 10), label="Select number of clusters:", value=5)
    dropdown
    return (dropdown,)


@app.cell
def _(df_feat_no_nans, dropdown):
    from sklearn import cluster

    k_means = cluster.KMeans(n_clusters=dropdown.value)
    k_means = k_means.fit(df_feat_no_nans)
    return (k_means,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visualizing the clustering

    To visualize the clustering, let's embed our dataframe into 2-D space using Principle Component Analysis (PCA).
    """)


@app.cell
def _(df_feat_no_nans, k_means, styling_utils):
    import numpy as np
    import plotly.express as px
    from sklearn import decomposition

    # Run PCA with 2 components
    pca = decomposition.PCA(n_components=2).fit_transform(df_feat_no_nans)

    # Create a color map for the labels
    labels = k_means.labels_.astype(str)
    color_map = styling_utils.get_color_map(np.unique(labels))

    # Plot as a scatter plot
    px.scatter(x=pca[:, 0], y=pca[:, 1], color=labels, color_discrete_map=color_map)


if __name__ == "__main__":
    app.run()
