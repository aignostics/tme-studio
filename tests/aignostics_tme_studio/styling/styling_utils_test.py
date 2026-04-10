import marimo as mo
import pytest

from aignostics_tme_studio.styling import styling_utils


@pytest.mark.unit
def test_get_aignx_logo() -> None:
    """Test the logo is loaded."""
    logo = styling_utils.get_aignx_logo()
    assert isinstance(logo, mo.Html)


@pytest.mark.unit
def test_load_css() -> None:
    """Test a css is loaded."""
    css = styling_utils.load_css()
    assert isinstance(css, mo.Html)


@pytest.mark.unit
def test_get_color_map() -> None:
    """Test the color map correctly cycles through the aignx colors."""
    n_colors = len(styling_utils.aignx_colors)
    classes = [f"class {i}" for i in range(n_colors * 2)]

    color_map = styling_utils.get_color_map(classes)
    assert len(color_map) == len(classes)

    # check the colors are in order
    colors = styling_utils.aignx_colors
    for i in range(3):
        assert color_map[classes[i]] == colors[i]

    # make sure the map is cycled; we start again with color 0
    assert color_map[classes[n_colors]] == colors[0]
