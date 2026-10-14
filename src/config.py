"""Central configuration for AI Flood Risk Mapping (B12-FAIR-AI-12)."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folders
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_SAMPLE = PROJECT_ROOT / "data" / "sample"
MODELS_DIR = PROJECT_ROOT / "models"
PLOTS_DIR = PROJECT_ROOT / "outputs" / "plots"
MAPS_DIR = PROJECT_ROOT / "outputs" / "maps"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

SAMPLE_DATA_PATH = DATA_SAMPLE / "flood_data_sample.csv"
PROCESSED_DATA_PATH = DATA_PROCESSED / "flood_data_processed.csv"
MODEL_PATH = MODELS_DIR / "flood_risk_model.pkl"
COMPARISON_PATH = REPORTS_DIR / "model_comparison.csv"
MAP_PATH = MAPS_DIR / "flood_risk_map.html"

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SAMPLES = 1500

TARGET_COL = "flood_risk"
CLASSES = ["LOW", "MEDIUM", "HIGH"]

NUMERIC_FEATURES = [
    "latitude",
    "longitude",
    "rainfall",
    "elevation",
    "slope",
    "distance_to_water",
    "drainage_density",
    "vegetation_index",
]

CATEGORICAL_FEATURES = ["land_use", "soil_type"]

ENGINEERED_FEATURES = [
    "runoff_index",
    "lowland_index",
    "drainage_proximity",
]

ALL_NUMERIC = NUMERIC_FEATURES + ENGINEERED_FEATURES

RISK_COLORS = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}

for _d in (DATA_RAW, DATA_PROCESSED, DATA_SAMPLE, MODELS_DIR,
           PLOTS_DIR, MAPS_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
