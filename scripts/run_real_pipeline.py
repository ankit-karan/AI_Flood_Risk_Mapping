"""REAL-DATA pipeline (primary mode): Sen1Floods11 + NASA POWER + SRTM.

Real flood observations + real rainfall + real elevation -> binary flood model
-> P(flood) -> LOW/MEDIUM/HIGH susceptibility bands -> real GIS map.
Writes data/real/real_features.csv, models/real_flood_model.pkl,
outputs/reports/real_model_comparison.csv, outputs/maps/real_flood_risk_map.html,
outputs/plots/real_*.png and data/real/data_manifest.json.
"""
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from src import real_config as rc
from src.utils import get_logger
from src.gee_data_access import gee_status
from src.sen1floods11_loader import download_label, read_label, label_stats
from src.spatial_sampling import sample_chip, spatial_split
from src.real_data_access import fetch_srtm_elevations, fetch_power_rain
from src.real_feature_engineering import slope_from_points, add_lowland_index
from src.real_data_preprocessing import clean_real
from src.real_model_pipeline import train_real, save_best_real, real_confusion_bands, CLASSES3
from src.real_mapping import create_real_map

logger = get_logger()
sns.set_theme(style="whitegrid")


def build_chip(chip: str) -> pd.DataFrame:
    tif = download_label(chip)
    arr, geo = read_label(tif)
    logger.info(f"{chip}: {label_stats(arr)}")
    df = sample_chip(tif, chip)
    lats = df["latitude"].to_numpy()
    lons = df["longitude"].to_numpy()
    df["elevation"] = fetch_srtm_elevations(lats, lons, chip)
    # NASA POWER is ~0.5 deg native: 2x2 query grid around chip, nearest assign.
    glats = np.array([lats.min(), lats.min(), lats.max(), lats.max()])
    glons = np.array([lons.min(), lons.max(), lons.min(), lons.max()])
    wstart, wend = rc.RAIN_WINDOWS.get(chip, (rc.RAIN_START, rc.RAIN_END))
    gs, gm = fetch_power_rain(glats, glons, wstart, wend, f"{chip}_{wstart}_{wend}")
    di = np.argmin((lats[:, None] - glats[None, :]) ** 2 + (lons[:, None] - glons[None, :]) ** 2, axis=1)
    df["rainfall_sum"] = np.round(gs[di], 2)
    df["rainfall_max"] = np.round(gm[di], 2)
    n_r, n_c = int(df["grid_h"].iloc[0]), int(df["grid_w"].iloc[0])
    df["slope"] = np.round(slope_from_points(
        df["elevation"].to_numpy(), lats, lons,
        df["grow"].to_numpy(), df["gcol"].to_numpy(), (n_r, n_c)), 3)
    return add_lowland_index(df)


def real_eda(df: pd.DataFrame):
    outdir = PROJECT_ROOT / "outputs" / "plots"
    outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.countplot(x="flooded", data=df, hue="flooded", legend=False,
                  palette={0: "steelblue", 1: "red"}, ax=ax)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["dry (0)", "flood (1)"])
    ax.set_title(f"Real class distribution ({rc.EVENT_NAME})")
    fig.tight_layout(); fig.savefig(outdir / "real_class_dist.png", dpi=130); plt.close(fig)
    for col, title in [("rainfall_sum", "NASA POWER 8-day rainfall (mm)"),
                       ("elevation", "SRTM elevation (m)"),
                       ("slope", "Slope from SRTM (deg)")]:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        sns.boxplot(x="flooded", y=col, data=df, hue="flooded", legend=False,
                    palette={0: "steelblue", 1: "red"}, ax=ax)
        ax.set_title(f"{title} — flood vs dry"); ax.set_xlabel("observed (0=dry, 1=flood)")
        fig.tight_layout()
        fig.savefig(outdir / f"real_{col}.png", dpi=130); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df[rc.REAL_NUMERIC + ["flooded"]].corr(numeric_only=True),
                annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Real-data correlation heatmap")
    fig.tight_layout(); fig.savefig(outdir / "real_correlation.png", dpi=130); plt.close(fig)
    logger.info("Real EDA plots saved.")


def write_manifest(df, train, test, comp, best) -> Path:
    manifest = {
        "project": "AI Flood Risk Mapping B12-FAIR-AI-12 — REAL DATA MODE",
        "event": rc.EVENT_NAME, "event_date": rc.EVENT_DATE,
        "rainfall_window": {"start": rc.RAIN_START, "end": rc.RAIN_END,
                            "aggregation": "daily sum + daily max of PRECTOTCORR"},
        "sentinel2_window_reference": list(rc.S2_WINDOW),
        "sources": {
            "flood_labels": {"name": "Sen1Floods11 v1.1 hand-labelled LabelHand",
                             "access": "public GCS bucket gs://sen1floods11 via STAC "
                                       + rc.STAC_COLLECTION_URL,
                             "values": "-1 nodata (dropped), 0 land, 1 water",
                             "resolution_m": 10, "crs": "EPSG:4326"},
            "rainfall": {"name": "NASA POWER daily PRECTOTCORR (mm/day)",
                         "access": "keyless REST point API",
                         "native_resolution_deg": 0.5,
                         "note": "NOT GPM IMERG; IMERG path lives in gee/rainfall.js"},
            "elevation": {"name": "SRTM v3 30m via OpenTopodata (no key)",
                          "slope": "finite-difference from SRTM grid (deg), "
                                   "same concept as ee.Terrain.slope"},
            "sentinel2": {"status": "NOT retrieved — needs GEE/SciHub auth; "
                                    "band-math + export code in gee/sentinel_features.js"},
        },
        "chips": {c: {"bbox": rc.CHIP_BBOX[c],
                      "split": "train" if c in rc.TRAIN_CHIPS else "test"} for c in
                  rc.TRAIN_CHIPS + rc.TEST_CHIPS},
        "sampling": f"every {rc.SAMPLING_STRIDE}th pixel per 512x512 chip; nodata dropped",
        "samples": {"total": len(df), "train": len(train), "test": len(test),
                    "train_water_frac": round(float(train['flooded'].mean()), 4),
                    "test_water_frac": round(float(test['flooded'].mean()), 4)},
        "features": rc.REAL_NUMERIC,
        "target": "flooded (binary Sen1Floods11 observation); bands LOW/MED/HIGH via "
                  f"pre-declared P(flood) edges {list(rc.BAND_EDGES)}",
        "split": "by chip (spatial): train chips vs held-out test chip; no adjacent-pixel split",
        "model_comparison": comp.to_dict(orient="records"),
        "best_model": best, "model_file": str(rc.REAL_MODEL_PATH),
        "map": str(rc.REAL_MAP_PATH),
        "processing_date": date.today().isoformat(),
        "disclaimer": "Academic prototype using event-specific observations; "
                      "not an operational flood-warning system.",
    }
    rc.REAL_MANIFEST_PATH.write_text(__import__("json").dumps(manifest, indent=2))
    return rc.REAL_MANIFEST_PATH


def main():
    logger.info("=== REAL-DATA pipeline: " + rc.EVENT_NAME + " ===")
    logger.info(f"GEE status: {gee_status()} (direct-download path used regardless)")
    if rc.GEE_EXPORT_PATH.exists():
        logger.info("GEE export CSV found — direct-download path still runs for audit; "
                    "see gee/README.md to switch fully.")
    frames = [build_chip(c) for c in rc.TRAIN_CHIPS + rc.TEST_CHIPS]
    df = clean_real(pd.concat(frames, ignore_index=True))
    df.to_csv(rc.REAL_FEATURES_PATH, index=False)
    logger.info(f"Real features: {len(df)} rows -> {rc.REAL_FEATURES_PATH}")
    real_eda(df)
    train, test = spatial_split(df)
    Xtr, ytr = train[rc.REAL_NUMERIC], train[rc.REAL_TARGET]
    Xte, yte = test[rc.REAL_NUMERIC], test[rc.REAL_TARGET]
    comp, fitted, proba = train_real(Xtr, ytr, Xte, yte)
    best = save_best_real(comp, fitted)
    # Confusion-matrix plot for the best model (band space)
    cm = real_confusion_bands(yte, proba[best])
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=CLASSES3, yticklabels=CLASSES3)
    ax.set_xlabel("Predicted band"); ax.set_ylabel("Reference band")
    ax.set_title(f"Real confusion (bands) — {best}")
    fig.tight_layout()
    fig.savefig(PROJECT_ROOT / "outputs" / "plots" / f"real_confusion_{best}.png", dpi=130)
    plt.close(fig)
    scored = df.copy()
    scored["p_flood"] = fitted[best].predict_proba(df[rc.REAL_NUMERIC])[:, 1]
    from src.real_model_pipeline import band_proba
    scored["susceptibility"] = band_proba(scored["p_flood"].to_numpy())
    create_real_map(scored)
    mp = write_manifest(df, train, test, comp, best)
    logger.info(f"=== Real pipeline complete. Manifest: {mp} ===")
    logger.info(comp.to_string(index=False))


if __name__ == "__main__":
    main()
