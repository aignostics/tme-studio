"""Unit tests for utils.py."""

import pytest
import yaml

from aignostics_tme_studio.utils import data_classes, utils


@pytest.mark.unit
def test_to_allcaps() -> None:
    """Test that to_allcaps correctly formats strings."""
    assert utils.to_allcaps("Carcinoma Cell") == "CARCINOMA_CELL"
    assert utils.to_allcaps("Stroma") == "STROMA"


@pytest.mark.parametrize(
    ("hex_color", "expected_rgb"),
    [
        ("#FFFFFF", (255, 255, 255)),
        ("#000000", (0, 0, 0)),
        ("FF0000", (255, 0, 0)),
        ("#00FF00", (0, 255, 0)),
        ("0000FF", (0, 0, 255)),
    ],
)
@pytest.mark.unit
def test_hex_to_rgb(hex_color: str, expected_rgb: tuple[int, int, int]) -> None:
    """Test correct conversion of a hex color string to an RGB tuple."""
    assert utils.hex_to_rgb(hex_color) == expected_rgb


@pytest.mark.unit
def test_load_features(tmpdir) -> None:
    """Test that the features config is loaded correctly."""
    config = {
        "features": {
            "my_features": [
                {
                    "name": "Relative Area",
                    "formatter": "RELATIVE_AREA_{tissue_cls}",
                    "unit": "%",
                },
                {
                    "name": "Density",
                    "formatter": "DENSITY_OF_{cell_cls}_{tissue_cls}",
                    "unit": "",
                },
            ]
        }
    }
    config_path = tmpdir / "features_config.yaml"
    yaml.dump(config, config_path.open("w"))
    features = utils.load_features(config_path)
    assert isinstance(features, dict)
    assert "my_features" in features
    assert isinstance(features["my_features"][0], data_classes.Feature)
