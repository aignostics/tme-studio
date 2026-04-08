"""Data sourcing configuration."""

REPO_ID = "aignostics/OpenTME"

TISSUE_FEATURES_FILES = "data/{}/tme_features_RUO.csv"

INDICATIONS = ["bladder_cancer", "breast_cancer", "lung_cancer", "colorectal_cancer", "liver_cancer"]

DEFAULT_INDICATION = INDICATIONS[0]

# Backward-compatible alias — resolves to the default tissue file.
FEATURES_FILENAME = TISSUE_FEATURES_FILES.format(DEFAULT_INDICATION)

CLASS_SETTINGS_FILENAME = "settings/model_output_classes.yaml"
FEAT_SETTINGS_FILENAME = "settings/tme_features.yaml"
