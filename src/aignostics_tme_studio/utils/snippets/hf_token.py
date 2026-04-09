import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("# Hugging Face token input")


@app.cell(hide_code=True)
def _(mo):
    # Get Hugging Face token
    _md = mo.md("""Enter your hugging face token in the below box to enable access to OpenTME.""")

    _acc = mo.accordion({"Click here for instructions to create a Hugging Face token": """Create an access token by going to [hf.co/settings/tokens](https://hf.co/settings/tokens)
        1. Go to "Repositories permissions".
        2. Select "datasets/Aignostics/OpenTME" and check boxes for read and view access.
        3. Click "create token". Enter your hugging face token in the below box to enable access to OpenTME.
                         """})
    hf_token = mo.ui.text(kind="password", label="Your HF Token from hf.co/settings/tokens")
    mo.vstack([_md, _acc, hf_token])
    return (hf_token,)


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
