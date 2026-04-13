import munch
import yaml

from .config import TISSUE_FEATURES_FILES
from .data_classes import Statistic


def load_munch(path: str) -> munch.Munch:
    """Load a YAML file and return a Munch object."""
    with open(path, encoding="utf-8") as stream:
        try:
            y = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return munch.Munch(y)


def load_statistics(path) -> list[Statistic]:
    """Load statistics from a yaml file and convert them to a list of Statistic objects."""
    stats_dict = load_munch(path)
    features = {}
    for _key, _features in stats_dict.items():
        features[_key] = [Statistic(**f) for f in _features]
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
    """Get features file for an indication."""
    # there are two placeholders that both are filled by the indication name.
    return TISSUE_FEATURES_FILES.format(indication, indication)
