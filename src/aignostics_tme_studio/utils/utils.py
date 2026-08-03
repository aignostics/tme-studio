"""Helpers to load feature definitions from YAML and format their names and colors."""

import munch
import yaml

from .config import TISSUE_FEATURES_FILES
from .data_classes import Feature


def load_munch(path: str) -> munch.Munch:
    """Load a YAML file and return a Munch object.

    Returns:
        The parsed YAML content, attribute-accessible.
    """
    with open(path, encoding="utf-8") as stream:
        return munch.Munch(yaml.safe_load(stream))


def load_features(path: str) -> dict:
    """Load features from a yaml file and convert them to a list of Feature objects.

    Returns:
        Lists of Feature objects, keyed by feature group.
    """
    features_dict = load_munch(path)
    features = {}
    for key, group in features_dict.items():
        features[key] = [Feature(**f) for f in group]
    return features


def hex_to_rgb(h: str) -> tuple[int, ...]:
    """Convert hexadecimal string to RBG tuple.

    Returns:
        R, G, B integer values.
    """
    if h[0] == "#":
        h = h[1:]
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def to_allcaps(s: str) -> str:
    """Return string capitalized and with spaces replaced by underscores."""
    return s.upper().replace(" ", "_")


def get_features_file_for_indication(indication: str) -> str:
    """Get features file for an indication.

    Returns:
        Path to the tissue features file of the indication.
    """
    # there are two placeholders that both are filled by the indication name.
    return TISSUE_FEATURES_FILES.format(indication, indication)
