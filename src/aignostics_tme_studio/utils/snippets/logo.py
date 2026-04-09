import marimo

__generated_with = "0.23.0"
app = marimo.App(width="medium")

@app.cell(hide_code=True)
def _(mo):
    mo.md("# Display logo")

@app.cell(hide_code=True)
def _():
    # Show logo
    from aignostics_tme_studio.styling import styling_utils

    styling_utils.get_aignx_logo()


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
