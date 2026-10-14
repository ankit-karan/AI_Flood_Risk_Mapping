"""Whole-India susceptibility pipeline: grid -> real env features -> predict -> map.

Grid cells get REAL features only (SRTM elevation/slope, NASA POWER rainfall,
reference week 20160805-20160812); S2 columns stay empty pending GEE backfill.
The trained real model (same 5 features) predicts P(flood) -> LOW/MEDIUM/HIGH.
Writes india_grid_features.csv, india_flood_predictions.csv, india map.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src import real_config as rc
from src.utils import get_logger
from src.india_grid import build_india_grid
from src.real_data_access import fetch_srtm_elevations, fetch_power_rain
from src.real_feature_engineering import add_lowland_index
from src.real_model_pipeline import band_proba

logger = get_logger()


def fetch_grid_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    lats = out["latitude"].to_numpy()
    lons = out["longitude"].to_numpy()
    out["elevation"] = fetch_srtm_elevations(lats, lons, "india_grid")
    # Slope via east/north lattice neighbours from the same fetched set.
    lut = {(round(lo, 4), round(la, 4)): e
           for lo, la, e in zip(lons, lats, out["elevation"].to_numpy())}
    step = rc.GRID_STEP_DEG
    m_lat = 111320.0
    slopes = np.full(len(out), np.nan)
    for i, (lo, la, e) in enumerate(zip(lons, lats, out["elevation"].to_numpy())):
        e_e = lut.get((round(lo + step, 4), round(la, 4)))
        e_n = lut.get((round(lo, 4), round(la + step, 4)))
        if e_e is not None and e_n is not None and np.isfinite([e, e_e, e_n]).all():
            m_lon = 111320.0 * max(0.2, abs(float(np.cos(np.radians(la)))))
            gx = (e_e - e) / (step * m_lon)
            gy = (e_n - e) / (step * m_lat)
            slopes[i] = float(np.degrees(np.arctan(np.hypot(gx, gy))))
    out["slope"] = np.round(slopes, 3)
    med = float(np.nanmedian(slopes))
    out["slope"] = out["slope"].fillna(round(med, 3))  # coastal cells; documented
    logger.info(f"Slope: {np.isfinite(slopes).sum()}/{len(out)} direct, "
                f"rest median-imputed ({med:.2f} deg)")
    # Rainfall: 1° POWER mesh over the grid bbox, nearest-assigned (documented).
    mglon, mglat = np.meshgrid(np.arange(rc.GRID_LON[0], rc.GRID_LON[1] + 1e-9, rc.RAIN_GRID_STEP),
                               np.arange(rc.GRID_LAT[0], rc.GRID_LAT[1] + 1e-9, rc.RAIN_GRID_STEP))
    gs, gm = fetch_power_rain(mglat.ravel(), mglon.ravel(),
                             rc.RAIN_START, rc.RAIN_END, "india_rainmesh")
    di = np.argmin((lats[:, None] - mglat.ravel()[None, :]) ** 2 +
                   (lons[:, None] - mglon.ravel()[None, :]) ** 2, axis=1)
    out["rainfall_sum"] = np.round(gs[di], 2)
    out["rainfall_max"] = np.round(gm[di], 2)
    out["rainfall_mean"] = np.round(gs[di] / 8.0, 2)
    out = add_lowland_index(out)
    for c in rc.S2_COLUMNS:
        out[c] = np.nan  # GEE-backfill reserved; NEVER synthesised
    return out


def flag_observed(df: pd.DataFrame) -> pd.Series:
    """Observed reference where a grid CELL AREA overlaps a Sen1Floods11 chip.

    Chips (~0.046°) are smaller than cells (0.1°), so point-in-bbox almost never
    hits; area-overlap (cell box intersects chip box) is the honest criterion —
    the cell genuinely contains observed labels.
    """
    half = rc.GRID_STEP_DEG / 2.0
    flags = []
    for _, r in df.iterrows():
        c0, c1 = r["longitude"] - half, r["longitude"] + half
        d0, d1 = r["latitude"] - half, r["latitude"] + half
        hit = [c for c, b in rc.CHIP_BBOX.items()
               if c0 <= b[2] and c1 >= b[0] and d0 <= b[3] and d1 >= b[1]]
        flags.append("chip:" + hit[0] if hit else "Not available for this location")
    return pd.Series(flags, index=df.index, name="observed_flood")


def main():
    import joblib
    logger.info("=== Whole-India susceptibility pipeline ===")
    grid = build_india_grid()
    feats = fetch_grid_features(grid)
    feats.to_csv(rc.INDIA_FEATURES_PATH, index=False)
    model = joblib.load(rc.REAL_MODEL_PATH)
    p = model.predict_proba(feats[rc.REAL_NUMERIC])[:, 1]
    pred = feats.copy()
    pred["predicted_flood_probability"] = np.round(p, 4)
    pred["risk_class"] = band_proba(p)
    pred["observed_flood"] = flag_observed(feats)
    cols = (["grid_id", "latitude", "longitude", "rainfall_sum", "rainfall_mean",
             "rainfall_max", "elevation", "slope"] + rc.S2_COLUMNS +
            ["predicted_flood_probability", "risk_class", "observed_flood"])
    pred[cols].to_csv(rc.INDIA_PREDICTIONS_PATH, index=False)
    counts = pred["risk_class"].value_counts()
    logger.info(f"India cells: {len(pred)} | bands: {counts.to_dict()}")
    from src.real_mapping import create_india_map
    create_india_map(pred)
    try:
        import json as _json
        m = _json.loads(rc.REAL_MANIFEST_PATH.read_text())
        m["india_grid"] = {
            "boundary": "GADM v4.1 India level-0 (" + rc.INDIA_BOUNDARY_URL + ")",
            "step_deg": rc.GRID_STEP_DEG,
            "cells": len(pred),
            "rain_mesh_step_deg": rc.RAIN_GRID_STEP,
            "rain_window": [rc.RAIN_START, rc.RAIN_END],
            "bands": counts.to_dict(),
            "s2_columns": "empty (NaN) — reserved for GEE backfill, never synthesised",
            "slope_note": "forward differences on fetched SRTM set; coastal cells median-imputed",
        }
        rc.REAL_MANIFEST_PATH.write_text(_json.dumps(m, indent=2))
    except Exception as e:
        logger.warning(f"manifest india update skipped: {e}")
    logger.info("=== India pipeline complete ===")


if __name__ == "__main__":
    main()
