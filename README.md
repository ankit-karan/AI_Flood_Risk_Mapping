# AI Flood Risk Mapping (B12 — FAIR-AI-12)

**Whole-India AI flood-susceptibility map from real geospatial data**,
with a labelled simulated fallback.

> ⚠️ Academic prototype — relative susceptibility, **not** an operational,
> real-time or emergency flood-warning system.

## A–D. Goal & REAL DATA vs SIMULATED DATA
Official goal: *create a basic flood-risk classification map.* Answered by
training on real Sen1Floods11 flood observations and predicting susceptibility
for a whole-India environmental grid.

| | REAL DATA (primary, default) | DEMO (fallback) |
|---|---|---|
| Labels | Sen1Floods11 LabelHand 0/1, Assam 2016 + Sri-Lanka 2017 (6 chips) | rule score → qcut |
| Rain | **PRIMARY: NASA GPM IMERG V07** (GEE path); executed: NASA POWER (documented) | simulated |
| Terrain | SRTM 30 m + derived slope | simulated |
| Vegetation/water/built | Sentinel-2 NDVI/NDWI/NDBI — code-ready, retrieval needs GEE auth | simulated NDVI |
| Boundary | GADM v4.1 India L0 | demo window |
| Model | `models/real_flood_model.pkl` | `models/flood_risk_model.pkl` |
| Maps | `outputs/maps/india_flood_risk_map.html` + `real_flood_risk_map.html` | `flood_risk_map.html` |
| Run | `run_real_pipeline.py` → `run_india_pipeline.py` | `run_pipeline.py` |

**PRIMARY REAL RAINFALL SOURCE: NASA GPM IMERG** (`NASA/GPM_L3/IMERG_V07`,
accumulated over each event window — executed in `gee/`, keyless POWER used
offline with identical schema). Sentinel-2 values are NEVER synthesised: columns
stay empty until `earthengine authenticate` + `scripts/gee_backfill_s2.py`.

## E. Architecture
```
Sen1Floods11 observed floods (Assam 2016 + Lanka 2017)
 + IMERG/POWER rain + SRTM elev/slope (+S2 after GEE auth)
 -> spatial join -> leakage-guarded preprocess -> chip-spatial split
 -> balanced LogReg/Tree/Forest -> P(flood) -> pre-declared bands
 -> whole-India 0.1° GADM grid prediction -> LOW/MEDIUM/HIGH
 -> india_flood_risk_map.html + dashboard
```

## F. Study/reference events & prediction area
Train/test: Assam chips 1072277/981708 + Lanka 551926/120804; held out:
591317 + Lanka 233609. Rain windows end ON each event date (20160805–12,
20170523–30). Prediction: whole India, 0.1° (~11 km) GADM-masked lattice.

## G–J. Preprocessing / features / models / evaluation
Median+scale pipelines; slope from SRTM; lowland_index; `assert_no_leakage`;
no qcut on real target; binary metrics + PR-AUC selection + band metrics.
Same 5 features train ↔ predict (S2 excluded until retrieved — consistency kept).

## K–L. Maps & dashboard (REAL default)
India map: whole-India view, band layers + rainfall + observed-chip overlays,
live counts, popups (P + band + observed YES/NO/Not-available). Dashboard pages:
Overview, Data Sources, Real Dataset, EDA, Model Performance,
India Flood Susceptibility Map, Location Prediction (nearest grid cell),
Methodology, About.

## M–N. GEE & Sen1Floods11 setup
`earthengine authenticate` (Google account via earthengine.google.com/signup) →
run `gee/*.js` in the Code Editor → optional CSV to `data/real/gee_export_features.csv`
→ `scripts/gee_backfill_s2.py` → re-run pipelines. Sen1Floods11: public GCS +
STAC, no key, handled by `src/sen1floods11_loader.py`.

## O. Commands
```bat
pip install -r requirements.txt
python scripts/run_real_pipeline.py    :: REAL training (6 chips, 2 events)
python scripts/run_india_pipeline.py   :: whole-India grid + map
python scripts/run_pipeline.py         :: DEMO fallback
python -m pytest tests/ -v
python -m streamlit run dashboard/app.py
python scripts/generate_report.py      :: FINAL real-results DOCX
```

## P–R. Outputs / limitations / references
`real_features.csv`, `india_grid_features.csv`, `india_flood_predictions.csv`,
`data_manifest.json`, both models, both maps, `real_*.png`, DOCX report.
Limits: 10 m labels vs 0.5° rain; S2 pending auth; 2 events; reference-week rain
snapshot; fixed bands; susceptibility ≠ warning. Land use via NDBI/NDVI path
(no fake columns); drainage via terrain proxies (no fake density).
Refs: Bonafilia et al. 2020; IMERG V07; POWER; SRTM; Sentinel-2; GEE; GADM v4.1.

## Team
Ankit (41), Anurag Anand (54), Aaditya Gautam (28), Nihaal Kumar Sharma (34).
