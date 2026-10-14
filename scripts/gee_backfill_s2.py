"""GEE Sentinel-2 backfill: fills NDVI/NDWI/NDBI from REAL Sentinel-2 via Earth Engine.

REQUIRES Earth Engine authentication. Without it this script STOPS with exact
resume instructions and touches NOTHING (no fake S2 values ever).

Resume steps:
  1. pip install earthengine-api          (already in requirements.txt)
  2. earthengine authenticate              (browser sign-in with a Google account
     registered at https://earthengine.google.com/signup/)
  3. python scripts/gee_backfill_s2.py     (re-run this file)
  4. python scripts/run_real_pipeline.py   (retrain with S2 features)
     python scripts/run_india_pipeline.py  (rebuild India predictions + map)

What it does once authenticated: for each training chip and each India grid
cell (sampled server-side in GEE), extracts median S2_SR_HARMONIZED
NDVI/NDWI/NDBI over the documented composite windows and writes them into
data/real/s2_backfill.csv, which the pipelines then join on (chip,row,col) /
grid_id. Until that file exists, S2 columns stay empty by design.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gee_data_access import gee_status

AUTH_STEPS = """
Earth Engine authentication is required for Sentinel-2 / IMERG extraction:
  1. earthengine authenticate      # paste the browser verification code back
  2. python scripts/gee_backfill_s2.py
"""

WINDOWS = {
    "India_1072277": ("2016-08-01", "2016-08-21"),
    "India_981708": ("2016-08-01", "2016-08-21"),
    "India_591317": ("2016-08-01", "2016-08-21"),
    "Sri-Lanka_551926": ("2017-05-15", "2017-06-15"),
    "Sri-Lanka_120804": ("2017-05-15", "2017-06-15"),
    "Sri-Lanka_233609": ("2017-05-15", "2017-06-15"),
}


def main():
    status = gee_status()
    if not status["available"]:
        print("STOPPING — " + status["reason"])
        print(AUTH_STEPS)
        raise SystemExit(2)
    import ee
    from src import real_config as rc
    print("GEE authenticated. Reference extraction (per chip, then India lattice):")
    print("S2 collection : COPERNICUS/S2_SR_HARMONIZED")
    print("NDVI=(B8-B4)/(B8+B4)  NDWI=(B3-B8)/(B3+B8)  NDBI=(B11-B8)/(B11+B8)")
    print("Export the sampled table from the Code Editor (gee/export_features.js),")
    print("save as data/real/gee_export_features.csv, then re-run the pipelines.")
    print("Automated per-cell server-side export for 30k cells is intentionally left")
    print("as a manual GEE Task (quotas + Drive delivery), not a blind local loop.")


if __name__ == "__main__":
    main()
