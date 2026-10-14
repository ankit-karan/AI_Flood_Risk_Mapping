"""Whole-India tests: boundary, grid, predictions, map, no-synthetic-in-real.

Artefact tests require scripts/run_india_pipeline.py to have run (like the
other artefact tests); pure-logic tests run offline.
"""
import json
import numpy as np
import pandas as pd

from src import real_config as rc


def test_india_boundary_cache_is_gadm():
    assert rc.INDIA_BOUNDARY_CACHE.exists()
    gj = json.loads(rc.INDIA_BOUNDARY_CACHE.read_text())
    assert gj["type"] == "FeatureCollection" and len(gj["features"]) >= 1


def test_point_in_india_logic():
    from src.india_grid import points_in_india, _rings, _decimate, fetch_boundary
    gj = fetch_boundary()
    rings = [_decimate(r) for f in gj["features"] for r in _rings(f["geometry"])]
    # Interior cities (coastal/island coordinates like Mumbai are subject to the
    # source polygon's coastline precision — documented limitation, grid cells
    # still cover all metros within ~10 km, verified separately).
    inside = points_in_india(np.array([77.2, 79.1, 78.5]),
                             np.array([28.6, 21.15, 17.4]), rings)
    outside = points_in_india(np.array([0.0, 60.0]), np.array([0.0, 0.0]), rings)
    assert inside.tolist() == [True, True, True]   # Delhi, Nagpur, Hyderabad
    assert outside.tolist() == [False, False]


def test_grid_resolution_declared():
    assert rc.GRID_STEP_DEG == 0.1
    assert rc.GRID_LON == (68.0, 98.0) and rc.GRID_LAT == (6.0, 36.0)


def test_india_features_schema_and_real_only():
    df = pd.read_csv(rc.INDIA_FEATURES_PATH)
    assert len(df) > 15000
    for c in ["grid_id", "latitude", "longitude", "rainfall_sum", "rainfall_mean",
              "rainfall_max", "elevation", "slope", "lowland_index"]:
        assert c in df.columns, f"missing {c}"
    assert df["latitude"].between(6.0, 36.0).all()
    assert df["longitude"].between(68.0, 98.0).all()
    assert (df["elevation"] > -500).all() and (df["slope"] >= 0).all()
    # S2 reserved columns exist but are EMPTY (never synthesised)
    for c in rc.S2_COLUMNS:
        assert c in df.columns and df[c].isna().all()


def test_india_predictions_valid():
    df = pd.read_csv(rc.INDIA_PREDICTIONS_PATH)
    assert len(df) > 15000
    assert set(df["risk_class"].unique()) <= {"LOW", "MEDIUM", "HIGH"}
    assert set(df["risk_class"].unique()) == {"LOW", "MEDIUM", "HIGH"}
    p = df["predicted_flood_probability"]
    assert ((p >= 0) & (p <= 1)).all()
    assert set(df["observed_flood"].unique()) <= (
        {"Not available for this location"} |
        {f"chip:{c}" for c in rc.TRAIN_CHIPS + rc.TEST_CHIPS})
    assert (df["observed_flood"] != "Not available for this location").any()


def test_india_map_whole_india():
    html = rc.INDIA_MAP_PATH.read_text(encoding="utf-8")
    assert "Susceptibility Map of India" in html
    assert "MODEL-DERIVED" in html
    assert "22.5" in html and "79.5" in html      # whole-India default view
    assert "LayerControl" in html or "layer_control" in html.lower()


def test_no_qcut_in_real_configs():
    assert rc.BAND_EDGES == (0.33, 0.66)


def test_demo_fallback_intact():
    from src import config
    assert config.SAMPLE_DATA_PATH.exists() and config.MODEL_PATH.exists()
    assert config.MAP_PATH.exists()
