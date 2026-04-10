"""Plot styling."""

import marimo as mo
import requests

from aignostics_tme_studio.utils import config

aignx_purple = "#483569"
aignx_pink = "#FF7EA5"
aignx_lilac = "#9B95EC"
aignx_pink_light = "#FF96B6"
aignx_orange = "#CA856A"
aignx_orange_dark = "#EE855D"
aignx_green = "#47A3A3"
aignx_blue = "#261C8D"
aignx_magenta = "#861F98"


aignx_colors = [aignx_lilac, aignx_pink, aignx_green, aignx_orange, aignx_magenta, aignx_blue, aignx_purple]


def get_aignx_logo() -> mo.Html:
    """Returns the Aignostics logo as a Marimo image component."""
    return mo.image(config.LOGO_FILE_PATH, width=150, style={"float": "right"})


def get_color_map(categories: list[str]) -> dict[str, str]:
    """Get a discrete color map for a list of categories."""
    color_map = {}
    for i, cat in enumerate(categories):
        color_map[cat] = aignx_colors[i % len(aignx_colors)]

    return color_map


def load_css() -> mo.Html:
    """Load stylesheet from github and return in HTML style tag."""
    css = requests.get(config.CSS_FILE_PATH, timeout=60).text
    return mo.Html(f"<style>{css}</style>")
