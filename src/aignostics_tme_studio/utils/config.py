"""Data sourcing configuration."""

REPO_ID = "aignostics/OpenTME"

TISSUE_FEATURES_FILES = "data/{}/tme_features_{}_RUO.csv"

INDICATIONS = ["bladder_cancer", "breast_cancer", "lung_cancer", "colorectal_cancer", "liver_cancer"]

DEFAULT_INDICATION = INDICATIONS[0]

CLASS_SETTINGS_FILENAME = "settings/model_output_classes.yaml"
FEAT_SETTINGS_FILENAME = "settings/tme_features.yaml"
