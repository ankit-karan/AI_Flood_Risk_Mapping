"""REAL-mode tests (offline): schema, leakage guard, banding, split, manifest.

These use tiny in-memory fixtures mirroring the real schema plus the ACTUAL
generated artefacts (real_features.csv, manifest, map, model) — no network.
"""
import json
import numpy as np
import pandas as pd
import pytest

from src import real_config as rc
from src.real_data_preprocessing import (assert_no_leakage, clean_real,
                                         get_real_preprocessor, FORBIDDEN_FEATURES)
from src.real_model_pipeline import band_proba, band_truth


@pytest.fixture
def mini():
    return pd.DataFrame({
        "chip": ["India_1072277"] * 4 + ["India_591317"] * 2,
        "row": [0, 0, 6, 6, 0, 6], "col": [0, 6, 0, 6, 0, 6],
        "longitude": [93.05] * 4 + [92.93] * 2,
        "latitude": [26.24] * 4 + [26.60] * 2,
        "flooded": [0, 1, 0, 1, 0, 1],
        "rainfall_sum": [70.0] * 6, "rainfall_max": [20.0] * 6,
        "elevation": [100.0, 60.0, 110.0, 55.0, 80.0, 50.0],
        "slope": [1.0, 0.5, 2.0, 0.4, 1.2, 0.6],
        "lowland_index": [0.7, 1.2, 0.6, 1.3, 0.9, 1.4],
    })


def test_real_schema(mini):
    assert set(rc.REAL_NUMERIC) <= set(mini.columns)
    assert set(mini["flooded"].unique()) <= {0, 1}


def test_no_target_leakage_allowed():
    with pytest.raises(ValueError):
        assert_no_leakage(rc.REAL_NUMERIC + ["flooded"])
    assert_no_leakage(rc.REAL_NUMERIC)  # real features pass


def test_forbidden_set_covers_label():
    assert {"flooded", "flood_risk", "susceptibility_score"} <= FORBIDDEN_FEATURES


def test_clean_real_drops_bad_rows(mini):
    bad = mini.copy()
    bad.loc[len(bad)] = bad.iloc[0]
    bad.loc[bad.index[-1], "flooded"] = 5
    out = clean_real(bad)
    assert (out["flooded"].isin([0, 1])).all()
    assert len(out) == len(mini)


def test_preprocessor_fits(mini):
    Xt = get_real_preprocessor().fit_transform(mini[rc.REAL_NUMERIC])
    assert Xt.shape[1] >= len(rc.REAL_NUMERIC)
    assert not np.isnan(np.asarray(Xt.todense() if hasattr(Xt, "todense") else Xt)).any()


def test_banding_predeclared_edges():
    assert rc.BAND_EDGES == (0.33, 0.66)
    assert list(band_proba(np.array([0.1, 0.5, 0.9]))) == ["LOW", "MEDIUM", "HIGH"]
    assert list(band_truth(np.array([0, 1]))) == ["LOW", "HIGH"]


def test_spatial_split_no_chip_overlap(mini):
    from src.spatial_sampling import spatial_split
    tr, te = spatial_split(mini)
    assert not set(tr["chip"]).intersection(set(te["chip"]))


def test_s2_helpers_are_pure_band_math():
    from src.real_feature_engineering import ndvi, ndwi, ndbi
    nir, red, green, swir = (np.array([0.4]), np.array([0.2]),
                             np.array([0.15]), np.array([0.3]))
    assert abs(ndvi(nir, red)[0] - (0.4 - 0.2) / 0.6) < 1e-9
    assert abs(ndwi(green, nir)[0] - (0.15 - 0.4) / 0.55) < 1e-9
    assert abs(ndbi(swir, nir)[0] - (0.3 - 0.4) / 0.7) < 1e-9


# --- Artefact tests (need scripts/run_real_pipeline.py to have run) ---
def test_real_features_file():
    df = pd.read_csv(rc.REAL_FEATURES_PATH)
    assert len(df) > 10000
    assert set(rc.REAL_NUMERIC + ["flooded", "chip"]) <= set(df.columns)
    assert set(df["chip"].unique()) == set(rc.TRAIN_CHIPS + rc.TEST_CHIPS)


def test_real_model_and_comparison():
    assert rc.REAL_MODEL_PATH.exists()
    comp = pd.read_csv(rc.REAL_COMPARISON_PATH)
    assert set(comp["model"]) == {"LogisticRegression", "DecisionTree", "RandomForest"}
    assert {"pr_auc", "roc_auc", "bin_f1", "band_f1_macro"} <= set(comp.columns)


def test_manifest_documents_sources():
    m = json.loads(rc.REAL_MANIFEST_PATH.read_text())
    assert "Sen1Floods11" in m["sources"]["flood_labels"]["name"]
    assert "POWER" in m["sources"]["rainfall"]["name"]
    assert "SRTM" in m["sources"]["elevation"]["name"]
    assert m["samples"]["total"] > 10000


def test_real_map_exists():
    html = rc.REAL_MAP_PATH.read_text(encoding="utf-8")
    assert "REAL DATA" in html and "Sen1Floods11" in html
