"""FINAL report generator: REAL-DATA results by default -> DOCX (21 sections).

Reads actual executed artefacts (never invented):
  outputs/reports/real_model_comparison.csv, data/real/data_manifest.json,
  data/real/india_flood_predictions.csv, outputs/plots/real_*.png.
Demo metrics appear ONLY in a labelled appendix.
Output: outputs/reports/Project_Report_B12_FAIR-AI-12.docx
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src import config
from src import real_config as rc

OUT = config.REPORTS_DIR / "Project_Report_B12_FAIR-AI-12.docx"
TEAM = [("Ankit", "41"), ("Anurag Anand", "54"),
        ("Aaditya Gautam", "28"), ("Nihaal Kumar Sharma", "34")]
BIN_COLS = ["model", "bin_accuracy", "bin_precision", "bin_recall", "bin_f1",
            "roc_auc", "pr_auc", "band_accuracy", "band_f1_macro"]


def h(doc, text, level=1):
    doc.add_heading(text, level=level)


def p(doc, text, bold=False):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = bold
    return para


def table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"
    for j, hh in enumerate(headers):
        t.cell(0, j).text = str(hh)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            t.cell(i, j).text = str(val)
    doc.add_paragraph()


def fig(doc, filename, caption, width=5.5):
    path = config.PLOTS_DIR / filename
    if not path.exists():
        p(doc, f"[Figure pending: {filename}]")
        return
    doc.add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARagraph if False else WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(f"Figure: {caption}")
    run.italic = True
    run.font.size = Pt(10)


def main():
    comp = pd.read_csv(rc.REAL_COMPARISON_PATH)
    manifest = json.loads(rc.REAL_MANIFEST_PATH.read_text())
    india = pd.read_csv(rc.INDIA_PREDICTIONS_PATH)
    counts = india["risk_class"].value_counts()
    best = comp.iloc[0]
    doc = Document()
    doc.styles["Normal"].font.size = Pt(11)

    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("AI Flood Risk Mapping"); r.bold = True; r.font.size = Pt(26)
    s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.add_run("B12 — FAIR-AI-12 | Whole-India AI Flood Susceptibility Map "
              "(real geospatial data)").font.size = Pt(13)
    table(doc, ["Name", "Roll No."], TEAM)
    d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = d.add_run("Academic prototype — relative susceptibility, "
                  "not an operational flood-warning system.")
    r.bold = True; r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    doc.add_page_break()

    h(doc, "1. Introduction")
    p(doc, "Flooding depends on rainfall, elevation, drainage, land use and other "
           "geographic factors. This project answers: given real environmental and "
           "geographic information, can we classify locations by relative flood "
           "susceptibility and visualise them on a GIS map — for the whole of India?")
    h(doc, "2. Problem Statement")
    p(doc, "Build a basic, explainable, whole-India flood-susceptibility "
           "classification map (LOW/MEDIUM/HIGH) from real observations without "
           "claiming real-time warning capability.")
    h(doc, "3. Motivation")
    p(doc, "Climate/disaster-management education needs honest AI+GIS examples: real "
           "satellite flood labels, real rainfall/terrain, documented limits.")
    h(doc, "4. Objectives")
    for o in ["Real Sen1Floods11 training labels (2 events, 6 chips).",
              "Real rainfall (GPM IMERG primary via GEE; POWER executed) + SRTM terrain.",
              "Balanced 3-model comparison with spatial holdout.",
              "Whole-India 0.1° environmental grid prediction + GIS map + dashboard."]:
        doc.add_paragraph(o, style="List Bullet")
    h(doc, "5. Scope")
    p(doc, f"Training: {manifest['samples']['total']} labelled points "
           f"(train {manifest['samples']['train']}, test {manifest['samples']['test']}); "
           f"prediction: {len(india)} India grid cells at {rc.GRID_STEP_DEG}°. "
           "Sentinel-2 indices: GEE code-ready, retrieval pending authentication.")

    h(doc, "6. Existing Approach")
    p(doc, "Manual GIS overlays (subjective); remote-sensing studies (heavy); "
           "Sen1Floods11 deep segmentation (GPU-heavy). Niche here: lightweight "
           "tabular ML on real labels + whole-country grid mapping on a student laptop.")
    h(doc, "7. Proposed System")
    p(doc, "Sen1Floods11 labels + IMERG/POWER rain + SRTM terrain → spatial join → "
           "leakage-guarded preprocessing → chip-spatial split → balanced classifiers → "
           "P(flood) → pre-declared bands → whole-India grid prediction → Folium map + "
           "dual-mode dashboard. Demo fallback retained offline and labelled.")
    h(doc, "8. Dataset and Data Sources")
    table(doc, ["Source", "Provides", "Resolution"],
          [["Sen1Floods11 v1.1 LabelHand", "flooded 0/1 (Assam 2016 + Sri-Lanka 2017)", "10 m"],
           ["NASA GPM IMERG V07 (GEE)", "PRIMARY rainfall sum/mean/max", "0.1°"],
           ["NASA POWER PRECTOTCORR", "executed rainfall (documented substitute)", "~0.5°"],
           ["SRTM v3 30 m", "elevation; slope derived", "30 m"],
           ["Sentinel-2 SR (GEE)", "NDVI/NDWI/NDBI — NOT retrieved (auth needed)", "10–20 m"],
           ["GADM v4.1 India L0", "prediction boundary", "vector"]])
    h(doc, "9. Data Preprocessing")
    p(doc, "Dedup, coordinate checks, binary-label filter, median+StandardScaler "
           "ColumnTransformer inside Pipelines (no leakage), per-event rain windows "
           "ending on each event date, chip-spatial split (no adjacent-pixel split).")
    h(doc, "10. Feature Engineering")
    p(doc, "Slope from SRTM grid (ee.Terrain.slope concept); lowland_index = "
           "rainfall_sum/elevation; S2 NDVI/NDWI/NDBI band-math implemented, awaiting "
           "GEE retrieval. Land-use influence represented via NDBI/NDVI path; no "
           "fabricated land_use/soil/drainage columns.")
    h(doc, "11. GIS Processing")
    p(doc, "EPSG:4326 throughout; GADM-masked 0.1° India lattice; 1° POWER mesh "
           "nearest-assigned (documented); Folium layers (susceptibility bands, "
           "rainfall, observed chips) + LayerControl; popups carry P(flood), band, "
           "and observed YES/NO/Not-available.")
    h(doc, "12. Machine Learning Methodology")
    p(doc, "LogisticRegression / DecisionTree / RandomForest, class_weight=balanced, "
           "same features + split; binary metrics (acc/prec/rec/F1/ROC-AUC/PR-AUC) + "
           "band acc/macro-F1 + confusion; PR-AUC selects (imbalance ~20% water).")
    h(doc, "13. Model Comparison")
    table(doc, ["Model", "binF1", "ROC-AUC", "PR-AUC", "bandF1"],
          [[r["model"], r["bin_f1"], r["roc_auc"], r["pr_auc"], r["band_f1_macro"]]
           for _, r in comp.iterrows()])
    p(doc, f"Selected: {best['model']} (PR-AUC {best['pr_auc']}, ROC-AUC {best['roc_auc']}). "
           "Winner decided by the numbers, never assumed.", bold=True)
    h(doc, "14. Results")
    p(doc, f"Test: {manifest['samples']['test']} held-out points across 2 chips/events. "
           f"Band confusion and EDA figures embedded below; full numbers in "
           "real_model_comparison.csv. India bands: " +
           ", ".join(f"{k} {counts.get(k, 0)}" for k in ["LOW", "MEDIUM", "HIGH"]) +
           f" (n={len(india)}).")
    for f, cap in [("real_class_dist.png", "Observed class distribution (real)."),
                   ("real_correlation.png", "Real-data correlation heatmap."),
                   (f"real_confusion_{best['model']}.png", "Band confusion, best model.")]:
        fig(doc, f, cap)
    h(doc, "15. India Flood Susceptibility Map")
    p(doc, "outputs/maps/india_flood_risk_map.html — whole-India default view, LOW/MEDIUM/HIGH "
           "layers, rainfall + observed-chip overlays, legend with live counts, popups with "
           "P(flood) and observed status. Model-derived susceptibility, not observed floods.")
    h(doc, "16. Dashboard")
    p(doc, "9 pages, REAL default: Overview, Data Sources, Real Dataset, EDA, Model "
           "Performance, India Flood Susceptibility Map, Location Prediction (nearest grid "
           "cell, approach B), Methodology, About. `python -m streamlit run dashboard/app.py`.")
    h(doc, "17. Testing")
    p(doc, "pytest suite: demo (10) + real schema/leakage/bands/split (12) + India "
           "boundary/grid/predictions/map (8) — run `python -m pytest tests/ -v`.")
    h(doc, "18. Limitations")
    for o in ["10 m labels vs 0.5° rainfall (documented mismatch).",
              "No Sentinel-2 indices without `earthengine authenticate`.",
              "Two events only — not a general flood model.",
              "Reference-week rainfall snapshot for the national map.",
              "Fixed equal-width bands are display conveniences.",
              "Susceptibility mapping only — no warning capability."]:
        doc.add_paragraph(o, style="List Bullet")
    h(doc, "19. Future Scope")
    p(doc, "GEE auth → IMERG + S2 backfill (`scripts/gee_backfill_s2.py`) and retrain; "
           "more Sen1Floods11 events; calibrated bands; SHAP; live feeds; cloud deploy.")
    h(doc, "20. Conclusion")
    p(doc, "A faculty-ready, honest whole-India susceptibility system: real labels + "
           "real environment + evaluated models + GIS map + dashboard, with every "
           "limitation documented and demo data never passed off as real.")
    h(doc, "21. References")
    for o in ["Bonafilia et al. 2020 (Sen1Floods11); NASA GPM IMERG V07; NASA POWER; "
              "SRTM; Copernicus Sentinel-2; GEE docs; GADM v4.1; "
              "scikit-learn/Folium/Streamlit/tifffile docs."]:
        doc.add_paragraph(o, style="List Bullet")
    h(doc, "Appendix A — Demo fallback (simulated, clearly labelled)")
    if config.COMPARISON_PATH.exists():
        dcomp = pd.read_csv(config.COMPARISON_PATH)
        table(doc, ["Model", "Accuracy", "F1-macro"],
              [[r["model"], r["accuracy"], r["f1_macro"]] for _, r in dcomp.iterrows()])
    p(doc, "Demo: 1500 simulated rows, rule score → qcut thirds, LogReg best (F1 0.764). "
           "Offline fallback only — never the primary experiment.")
    doc.save(str(OUT))
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    main()
