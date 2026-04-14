"""Data sourcing configuration."""

REPO_ID = "aignostics/OpenTME"

TISSUE_FEATURES_FILES = "data/{}/tme_features_{}_RUO.csv"

INDICATIONS = ["bladder_cancer", "breast_cancer", "lung_cancer", "colorectal_cancer", "liver_cancer"]

THUMBNAIL_FILES = ["wsi.png", "tissue_qc.png", "tissue_segmentation.png", "cell_classification.png"]

DEFAULT_INDICATION = INDICATIONS[0]

MODEL_SETTINGS_FILENAME = "settings/model_variables.yaml"
FEAT_SETTINGS_FILENAME = "settings/tme_features.yaml"

# Files need to be loaded over HTTP to allow loading in molab
METADATA_FILE_PATH = "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/notebooks/tutorials/public/metadata.csv?raw=true"
LOGO_FILE_PATH = "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/styling/images/logo_lavender.png?raw=true"
CSS_FILE_PATH = (
    "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/styling/style.css?raw=true"
)
