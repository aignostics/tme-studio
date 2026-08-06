"""Data sourcing configuration."""

REPO_ID = "aignostics/OpenTME"

TISSUE_FEATURES_FILES = "data/{}/tme_features_{}_RUO.csv"

# Whole-tumor-region cell features (concentric-zone readouts: tumor core, inner/outer invasive
# margin, extratumoral tissue), used by the IDE immune-phenotype analysis.
WHOLE_TUMOR_REGION_CELL_FEATURES_FILES = "data/{}/whole_tumor_region_cell_features_{}_RUO.csv"

INDICATIONS = ["bladder_cancer", "breast_cancer", "lung_cancer", "colorectal_cancer", "liver_cancer"]

THUMBNAIL_FILES = ["wsi.png", "tissue_qc.png", "tissue_segmentation.png", "cell_classification.png"]

DEFAULT_INDICATION = INDICATIONS[0]

# cBioPortal public REST API, used to fetch harmonized TCGA overall-survival endpoints that are not
# shipped with OpenTME (see the `survival_analysis` and `ide_immune_phenotypes` example notebooks).
CBIOPORTAL_API_URL = "https://www.cbioportal.org/api"

# Column carrying the neoadjuvant-treatment history flag in cBioPortal PATIENT clinical data.
NEOADJUVANT_COLUMN = "HISTORY_NEOADJUVANT_TRTYN"

# Map each OpenTME indication to the TCGA PanCancer Atlas study id(s) on cBioPortal. Lung pools the
# adenocarcinoma (LUAD) and squamous-cell (LUSC) cohorts, matching the OpenTME `lung_cancer` features.
CBIOPORTAL_STUDIES = {
    "bladder_cancer": ["blca_tcga_pan_can_atlas_2018"],
    "breast_cancer": ["brca_tcga_pan_can_atlas_2018"],
    "lung_cancer": ["luad_tcga_pan_can_atlas_2018", "lusc_tcga_pan_can_atlas_2018"],
    "colorectal_cancer": ["coadread_tcga_pan_can_atlas_2018"],
    "liver_cancer": ["lihc_tcga_pan_can_atlas_2018"],
    "pancreatic_cancer": ["paad_tcga_pan_can_atlas_2018"],
    "prostate_cancer": ["prad_tcga_pan_can_atlas_2018"],
    "stomach_cancer": ["stad_tcga_pan_can_atlas_2018"],
}

MODEL_SETTINGS_FILENAME = "settings/model_variables.yaml"
FEAT_SETTINGS_FILENAME = "settings/tme_features.yaml"

# Files need to be loaded over HTTP to allow loading in molab
METADATA_FILE_PATH = "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/notebooks/tutorials/public/metadata.csv?raw=true"
LOGO_FILE_PATH = "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/styling/images/logo_lavender.png?raw=true"
CSS_FILE_PATH = (
    "https://github.com/aignostics/tme-studio/blob/main/src/aignostics_tme_studio/styling/style.css?raw=true"
)
