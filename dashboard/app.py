"""Streamlit dashboard — AI Flood Risk Mapping (B12-FAIR-AI-12).

REAL DATA is the default mode (Sen1Floods11 + NASA POWER + SRTM + GEE reference).
DEMO mode (simulated data) remains for offline fallback — every DEMO page says so.
Observation vs prediction are never mixed: chip maps = observed reference zones,
India map = MODEL-DERIVED susceptibility.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import config
from src import real_config as rc
from src.prediction import predict_single

st.set_page_config(page_title="AI Flood Risk Mapping", layout="wide")
TEAM = [["Ankit", 41], ["Anurag Anand", 54],
        ["Aaditya Gautam", 28], ["Nihaal Kumar Sharma", 34]]
WARN = "Academic prototype — relative susceptibility, not an operational warning system."
PRED_NOTE = ("MODEL-DERIVED susceptibility. Flood observations exist only for "
             "labelled Sen1Floods11 reference events.")


@st.cache_data
def load_demo():
    if config.PROCESSED_DATA_PATH.exists():
        return pd.read_csv(config.PROCESSED_DATA_PATH)
    if config.SAMPLE_DATA_PATH.exists():
        return pd.read_csv(config.SAMPLE_DATA_PATH)
    return pd.DataFrame()


@st.cache_data
def load_demo_comp():
    return pd.read_csv(config.COMPARISON_PATH) if config.COMPARISON_PATH.exists() else pd.DataFrame()


@st.cache_data
def load_real():
    return pd.read_csv(rc.REAL_FEATURES_PATH) if rc.REAL_FEATURES_PATH.exists() else pd.DataFrame()


@st.cache_data
def load_real_comp():
    return pd.read_csv(rc.REAL_COMPARISON_PATH) if rc.REAL_COMPARISON_PATH.exists() else pd.DataFrame()


@st.cache_data
def load_india():
    return pd.read_csv(rc.INDIA_PREDICTIONS_PATH) if rc.INDIA_PREDICTIONS_PATH.exists() else pd.DataFrame()


@st.cache_data
def load_manifest():
    return json.loads(rc.REAL_MANIFEST_PATH.read_text()) if rc.REAL_MANIFEST_PATH.exists() else {}


df, comp = load_demo(), load_demo_comp()
rdf, rcomp, india, manifest = load_real(), load_real_comp(), load_india(), load_manifest()

st.sidebar.title("🌊 AI Flood Risk Mapping")
st.sidebar.caption("B12 — FAIR-AI-12")
mode = st.sidebar.radio("Mode", ["REAL DATA", "DEMO"], index=0,
                        help="REAL DATA = real geospatial data (default). DEMO = simulated fallback.")
PAGES = ["Overview", "Data Sources", "Real Dataset", "EDA", "Model Performance",
         "India Flood Susceptibility Map", "Location Prediction",
         "Methodology", "About"]
page = st.sidebar.radio("Navigate", PAGES)
REAL = (mode == "REAL DATA")
st.sidebar.info(f"📌 Active: **{mode}**\n\n{WARN}")

# ============================ pages ============================
if page == "Overview":
    st.title("🌊 AI Flood Risk Mapping")
    if REAL:
        st.success(f"**Real geospatial data.** {PRED_NOTE}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Training samples (real)", len(rdf))
        c2.metric("India grid cells", len(india))
        c3.metric("Events", "Assam 2016 + Sri-Lanka 2017")
        c4.metric("Best model", rcomp.iloc[0]["model"] if not rcomp.empty else "—")
        st.markdown("""Trained on **real observed floods** (Sen1Floods11) with real
        rainfall (NASA POWER; IMERG via GEE reference) and SRTM terrain, then applied
        to a real **whole-India environmental grid** → relative susceptibility map.""")
    else:
        st.warning("**DEMO MODE — simulated/demo data for academic prototyping.**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", len(df))
        c2.metric("Features", 10)
        c3.metric("Classes", 3)
        c4.metric("Best model", comp.iloc[0]["model"] if not comp.empty else "—")
    st.subheader("Team")
    st.table(pd.DataFrame(TEAM, columns=["Name", "Roll No."]))

elif page == "Data Sources":
    st.header("Data Sources")
    st.table(pd.DataFrame([
        ["Sen1Floods11 v1.1 LabelHand", "REAL observed flood reference (0/1)",
         "public GCS + STAC, no key", "10 m", "REAL"],
        ["NASA GPM IMERG V07 (GEE)", "PRIMARY rainfall: sum/mean/max (mm)",
         "needs `earthengine authenticate`", "0.1°", "REAL (GEE path)"],
        ["NASA POWER PRECTOTCORR", "executed rainfall (documented substitute)",
         "keyless REST", "~0.5° daily", "REAL (executed)"],
        ["SRTM v3 30 m", "elevation (m); slope derived", "keyless (OpenTopodata) / GEE",
         "30 m", "REAL"],
        ["Sentinel-2 SR (GEE)", "NDVI/NDWI/NDBI — code-ready, NOT retrieved",
         "needs GEE auth", "10–20 m", "REFERENCE ONLY"],
        ["GADM v4.1 India L0", "whole-India boundary", "keyless download", "vector",
         "REAL"],
        ["Simulated generator", "10 demo features", "local code", "n/a", "DEMO"],
    ], columns=["Source", "Provides", "Access", "Resolution", "Used in"]))

elif page == "Real Dataset":
    st.header("Real Dataset")
    if REAL:
        if rdf.empty:
            st.warning("Run `python scripts/run_real_pipeline.py` first.")
        else:
            st.success("**Real geospatial data.**")
            st.write(f"Rows **{len(rdf)}** | train {rc.TRAIN_CHIPS} | test {rc.TEST_CHIPS} | "
                     f"water frac **{rdf['flooded'].mean():.3f}**")
            st.dataframe(rdf.head(50), use_container_width=True)
            st.bar_chart(rdf["flooded"].value_counts().rename({0: "dry (observed)", 1: "flood (observed)"}))
            if manifest:
                st.subheader("Manifest highlights")
                st.json({k: manifest[k] for k in
                         ["event", "event_date", "rainfall_window", "samples", "best_model"]
                         if k in manifest})
                if "india_grid" in manifest:
                    st.json(manifest["india_grid"])
    else:
        st.warning("**DEMO MODE — simulated/demo data for academic prototyping.**")
        st.write(f"Rows: **{len(df)}** | Columns: **{len(df.columns)}**")
        st.dataframe(df.head(50), use_container_width=True)

elif page == "EDA":
    st.header(f"EDA — {'Real geospatial data' if REAL else 'DEMO (simulated)'}")
    if REAL:
        for f in ["real_class_dist.png", "real_rainfall_sum.png", "real_elevation.png",
                  "real_slope.png", "real_correlation.png"]:
            p = config.PLOTS_DIR / f
            if p.exists():
                st.subheader(f.replace("real_", "").replace(".png", "").replace("_", " ").title())
                st.image(str(p), use_container_width=True)
        if rdf.empty:
            st.warning("Run `python scripts/run_real_pipeline.py` first.")
    else:
        st.warning("**DEMO MODE — simulated/demo data.**")
        for img in sorted(config.PLOTS_DIR.glob("*.png")):
            if img.name.startswith("real_"):
                continue
            st.subheader(img.stem.replace("_", " ").title())
            st.image(str(img), use_container_width=True)

elif page == "Model Performance":
    st.header(f"Model Performance — {mode}")
    if REAL:
        st.success("**Real geospatial data.** Chip-spatial split: numbers estimate transfer to new areas.")
        if rcomp.empty:
            st.warning("Run `python scripts/run_real_pipeline.py` first.")
        else:
            st.dataframe(rcomp, use_container_width=True)
            for img in sorted(config.PLOTS_DIR.glob("real_confusion_*.png")):
                st.subheader("Confusion (bands) — best model")
                st.image(str(img))
    else:
        st.warning("**DEMO MODE — simulated-data metrics.**")
        if not comp.empty:
            st.dataframe(comp, use_container_width=True)
            for img in sorted(config.PLOTS_DIR.glob("confusion_*.png")):
                st.subheader(img.stem.replace("_", " ").title())
                st.image(str(img))

elif page == "India Flood Susceptibility Map":
    st.header("AI-Based Flood Susceptibility Map of India")
    if REAL:
        st.success(f"**Real geospatial data.** {PRED_NOTE}")
        if rc.INDIA_MAP_PATH.exists():
            components.html(rc.INDIA_MAP_PATH.read_text(encoding="utf-8"),
                            height=650, scrolling=True)
        else:
            st.warning("India map not built yet. Run `python scripts/run_india_pipeline.py`.")
        with st.expander("Reference: Sen1Floods11 chip zones (observed labels)"):
            if config.MAPS_DIR.joinpath("real_flood_risk_map.html").exists():
                components.html(
                    config.MAPS_DIR.joinpath("real_flood_risk_map.html").read_text(encoding="utf-8"),
                    height=500, scrolling=True)
    else:
        st.warning("**DEMO MODE — simulated/demo data.**")
        if config.MAP_PATH.exists():
            components.html(config.MAP_PATH.read_text(encoding="utf-8"), height=600, scrolling=True)

elif page == "Location Prediction":
    st.header("Location Prediction")
    if REAL:
        st.success("**Real geospatial data.** Approach B: nearest whole-India grid cell "
                   "(real env features) → trained model → probability + band.")
        if india.empty:
            st.warning("Run `python scripts/run_india_pipeline.py` first.")
        else:
            la = st.number_input("Latitude", 6.5, 35.5, 26.2)
            lo = st.number_input("Longitude", 68.0, 97.5, 93.06)
            if st.button("Classify location"):
                d2 = (india["latitude"] - la) ** 2 + (india["longitude"] - lo) ** 2
                r = india.loc[d2.idxmin()]
                color = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}[r["risk_class"]]
                st.markdown(f"### Susceptibility: :{color}[{r['risk_class']}] "
                            f"(P={r['predicted_flood_probability']:.3f})")
                st.write(f"Nearest grid cell {int(r['grid_id'])} @ "
                         f"({r['latitude']:.3f}, {r['longitude']:.3f}); "
                         f"rain {r['rainfall_sum']} mm, elev {r['elevation']} m, "
                         f"slope {r['slope']}°. Observed flood: {r['observed_flood']}.")
    else:
        st.warning("**DEMO MODE — simulated/demo model.**")
        with st.form("pred"):
            c1, c2 = st.columns(2)
            with c1:
                rainfall = st.slider("Rainfall (mm)", 300, 3500, 1400)
                elevation = st.slider("Elevation (m)", 5, 1200, 150)
                slope = st.slider("Slope (deg)", 0.0, 35.0, 5.0)
                distance_to_water = st.slider("Distance to water (km)", 0.0, 20.0, 2.0)
                drainage_density = st.slider("Drainage density", 0.3, 5.0, 2.2)
            with c2:
                land_use = st.selectbox("Land use",
                    ["Agriculture", "Urban", "Forest", "Wetland", "Barren"])
                soil_type = st.selectbox("Soil type", ["Clay", "Loam", "Silt", "Sand"])
                vegetation_index = st.slider("NDVI", 0.05, 0.95, 0.45)
                latitude = st.number_input("Latitude", 18.0, 28.0, 19.07)
                longitude = st.number_input("Longitude", 72.0, 80.0, 72.87)
            if st.form_submit_button("Classify"):
                try:
                    label = predict_single({
                        "latitude": latitude, "longitude": longitude, "rainfall": rainfall,
                        "elevation": elevation, "slope": slope,
                        "distance_to_water": distance_to_water,
                        "drainage_density": drainage_density, "land_use": land_use,
                        "soil_type": soil_type, "vegetation_index": vegetation_index})
                    color = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}.get(label, "blue")
                    st.markdown(f"### Predicted risk: :{color}[{label}]")
                except FileNotFoundError as e:
                    st.error(str(e))

elif page == "Methodology":
    st.header("Methodology")
    st.markdown(f"""**REAL:** Sen1Floods11 binary labels (Assam 2016 + Sri-Lanka 2017) →
    NASA POWER event-locked rainfall + SRTM elevation/derived slope + lowland index
    → chip-spatial split (train {len(rc.TRAIN_CHIPS)} chips / test {len(rc.TEST_CHIPS)} chips)
    → balanced LogReg/Tree/Forest → P(flood) → pre-declared bands {list(rc.BAND_EDGES)}
    → whole-India 0.1° GADM-masked grid prediction → susceptibility map.
    Guards: leakage assertions, no qcut, no future data, PR-AUC selection.
    S2 indices: GEE code-complete, retrieval needs `earthengine authenticate`.
    **DEMO:** rule score → qcut thirds (fallback only).""")

else:
    st.header("About")
    st.markdown("""**AI Flood Risk Mapping (B12-FAIR-AI-12)** — B.Tech IT Sem V AIML PBL.
    Real: Sen1Floods11 (Bonafilia et al. 2020), NASA GPM IMERG (GEE) / POWER
    (executed), SRTM, Sentinel-2 (GEE reference), GADM boundary.
    Stack: Python, scikit-learn, folium, streamlit, tifffile, earthengine-api.""")
    st.table(pd.DataFrame(TEAM, columns=["Name", "Roll No."]))
    st.caption(WARN)
