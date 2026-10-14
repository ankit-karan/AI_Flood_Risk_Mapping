"""Central configuration for the REAL-DATA pipeline (primary mode).

Study area chosen from ACTUAL Sen1Floods11 v1.1 STAC metadata
(https://storage.googleapis.com/sen1floods11/v1.1/catalog/catalog.json):
event 'India', Sentinel-1/2 date 2016-08-12 (Assam/Brahmaputra valley floods).

Chips selected from a survey of 10 random India label chips on 2026-10-07:
moderate water fraction + low nodata for training, one distant high-water
chip held out as the spatial test set (prevents spatial leakage).
"""
from pathlib import Path

from .config import PROJECT_ROOT  # noqa: F401 (keeps one root definition)

DATA_REAL = PROJECT_ROOT / "data" / "real"
CACHE_DIR = DATA_REAL / "cache"

REAL_FEATURES_PATH = DATA_REAL / "real_features.csv"
REAL_MODEL_PATH = PROJECT_ROOT / "models" / "real_flood_model.pkl"
REAL_COMPARISON_PATH = PROJECT_ROOT / "outputs" / "reports" / "real_model_comparison.csv"
REAL_MAP_PATH = PROJECT_ROOT / "outputs" / "maps" / "real_flood_risk_map.html"
REAL_MANIFEST_PATH = DATA_REAL / "data_manifest.json"
GEE_EXPORT_PATH = DATA_REAL / "gee_export_features.csv"  # optional manual GEE export

STAC_COLLECTION_URL = ("https://storage.googleapis.com/sen1floods11/v1.1/catalog/"
                       "sen1floods11_hand_labeled_label/collection.json")
GCS_TIF_TEMPLATE = ("https://storage.googleapis.com/sen1floods11/v1.1/data/"
                    "flood_events/HandLabeled/LabelHand/{chip}_LabelHand.tif")

# --- Event / temporal definition (all features are <= event date) ---
EVENT_NAME = "Sen1Floods11 India 2016-08-12 (Assam/Brahmaputra valley)"
EVENT_DATE = "2016-08-12"
RAIN_START = "20160805"   # NASA POWER format YYYYMMDD
RAIN_END = "20160812"     # 8-day pre-event window, ends ON the event date
S2_WINDOW = ("2016-08-01", "2016-08-20")  # GEE Sentinel-2 composite window (reference only)

# --- Chip split: train on 4 chips (2 events), test on 2 held-out chips (spatial + event transfer) ---
TRAIN_CHIPS = ["India_1072277", "India_981708", "Sri-Lanka_551926", "Sri-Lanka_120804"]
TEST_CHIPS = ["India_591317", "Sri-Lanka_233609"]
CHIP_BBOX = {  # [minlon, minlat, maxlon, maxlat] from STAC items
    "India_1072277": [93.04534117241815, 26.21643325174411, 93.09133491496507, 26.262426994291033],
    "India_981708": [93.78124105316886, 26.40040822193179, 93.82723479571578, 26.446401964478714],
    "India_591317": [92.90735994477738, 26.584383192119468, 92.95335368732431, 26.63037693466639],
    "Sri-Lanka_551926": [81.45491805059443, 7.9569174606170705, 81.50091179314136, 8.002911203163993],
    "Sri-Lanka_120804": [81.04097436767216, 7.634961262788634, 81.08696811021909, 7.680955005335557],
    "Sri-Lanka_233609": [81.08696811021908, 7.818936232976312, 81.132961852766, 7.864929975523235],
}
# Per-event rainfall windows (NASA POWER YYYYMMDD): 8 days ending ON each event date.
# Assam event 2016-08-12; Sri-Lanka event (S1 2017-05-30).
RAIN_WINDOWS = {
    "India_1072277": ("20160805", "20160812"),
    "India_981708": ("20160805", "20160812"),
    "India_591317": ("20160805", "20160812"),
    "Sri-Lanka_551926": ("20170523", "20170530"),
    "Sri-Lanka_120804": ("20170523", "20170530"),
    "Sri-Lanka_233609": ("20170523", "20170530"),
}
# Fallback single window (India-wide grid uses the reference flood week).
RAIN_START = "20160805"
RAIN_END = "20160812"

# --- Whole-India prediction grid ---
INDIA_BOUNDARY_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_0.json"
INDIA_BOUNDARY_CACHE = DATA_REAL / "cache" / "india_boundary.geojson"
GRID_STEP_DEG = 0.1          # ~11 km cells; honest vs 0.5° rain and 30 m SRTM
GRID_LON = (68.0, 98.0)
GRID_LAT = (6.0, 36.0)
RAIN_GRID_STEP = 1.0         # NASA POWER sampling mesh; nearest-assigned to cells
INDIA_FEATURES_PATH = DATA_REAL / "india_grid_features.csv"
INDIA_PREDICTIONS_PATH = DATA_REAL / "india_flood_predictions.csv"
INDIA_MAP_PATH = PROJECT_ROOT / "outputs" / "maps" / "india_flood_risk_map.html"
INDIA_CENTER = [22.5, 79.5]

# Sentinel-2 columns: reserved for the GEE backfill (scripts/gee_backfill_s2.py).
# Until retrieval they stay EMPTY (NaN) — never synthesised. The executed model
# does not use them (feature consistency training <-> prediction).
S2_COLUMNS = ["NDVI", "NDWI", "NDBI"]

SAMPLING_STRIDE = 6        # every 6th pixel of the 512x512 chip (~85x85 grid)
RANDOM_STATE = 42

# --- Feature schema (real sources only) ---
REAL_NUMERIC = ["rainfall_sum", "rainfall_max", "elevation", "slope", "lowland_index"]
REAL_TARGET = "flooded"    # 1 = water/flood, 0 = land (Sen1Floods11 LabelHand)

# Pre-declared equal-width susceptibility bands on P(flood). Declared here BEFORE
# any model was trained — not tuned to force equal class counts.
BAND_EDGES = (0.33, 0.66)

REAL_DATA_ENABLED = True   # pipeline auto-falls back to demo mode if artefacts missing

for _d in (DATA_REAL, CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)
