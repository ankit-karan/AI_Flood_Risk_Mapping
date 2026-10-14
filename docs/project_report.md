# Project Report — AI Flood Risk Mapping (B12-FAIR-AI-12)

Team: Ankit (41), Anurag Anand (54), Aaditya Gautam (28), Nihaal Kumar Sharma (34).
B.Tech IT Semester V — AIML PBL. **Real-data primary (Sen1Floods11 + NASA
rainfall + SRTM); simulated fallback labelled as such. Academic prototype —
not an operational flood-warning system.**

## 1. Introduction
Given real environmental/geographic information, can we classify locations by
relative flood susceptibility and map them for the whole of India? Yes — with
documented limits — using real flood observations, real rainfall/terrain, an
evaluated classifier, and a GIS map.

## 2. Problem Statement
Build a basic, explainable whole-India flood-susceptibility classification map
(LOW/MEDIUM/HIGH) from real data, presented as a map rather than any warning system.

## 3. Motivation
Disaster/climate education needs honest AI+GIS examples combining real satellite
observations with ML — including explicit statements of what the system cannot do.

## 4. Objectives
Real Sen1Floods11 labels (2 events, 6 chips); real rainfall (IMERG primary, POWER
executed) + SRTM terrain; 3-model comparison under spatial holdout; whole-India
0.1° grid prediction; interactive map + dual-mode dashboard.

## 5. Scope
Training: 42,694 labelled points (train 28,490 / test 14,204). Prediction:
~27.9k India cells at 0.1° (~11 km). S2 indices pending GEE auth. One reference
rain week for the national snapshot.

## 6. Existing Approach
Manual GIS overlays (subjective); remote-sensing studies (heavy); Sen1Floods11
deep segmentation (GPU-heavy). Niche: laptop-runnable tabular ML on real labels
with country-scale grid mapping.

## 7. Proposed System
Sen1Floods11 + IMERG/POWER + SRTM (+S2 after auth) → spatial/temporal join →
leakage-guarded preprocessing → chip-spatial split → balanced classifiers →
P(flood) → pre-declared bands → India grid → Folium map + dashboard. GEE scripts
are the full-resolution reference layer; demo fallback stays offline.

## 8. Dataset and Data Sources
Sen1Floods11 v1.1 LabelHand (Assam 2016-08-12: chips 1072277/981708/591317;
Sri-Lanka 2017-05-30: 551926/120804/233609); NASA GPM IMERG V07 accumulated per
event window (PRIMARY, GEE); NASA POWER PRECTOTCORR (executed substitute,
labelled); SRTM 30 m; Sentinel-2 SR band math (code-ready, not retrieved);
GADM v4.1 India boundary. Manifest: `data/real/data_manifest.json`.

## 9. Data Preprocessing
Dedup, coordinate checks, binary-label filter, median+StandardScaler pipelines
(train-fit only), per-event rain windows ending on event dates, chip+event holdout
(4 train / 2 test chips), leakage assertions in code and tests.

## 10. Feature Engineering
Slope from SRTM grid; lowland_index = rainfall_sum/elevation; S2
NDVI/NDWI/NDBI formulas implemented for real bands. No invented
land_use/soil/drainage columns (represented via NDBI/NDVI path + terrain proxies).

## 11. GIS Processing
EPSG:4326; GADM-masked 0.1° lattice (27,857 cells); 1° POWER mesh
nearest-assigned (documented); Folium band/rainfall/observed-chip layers +
LayerControl; popups with P(flood), band, observed YES/NO/Not-available.

## 12. Machine Learning Methodology
LogReg/Tree/Forest, class_weight=balanced, identical 5 features train↔predict;
binary acc/prec/rec/F1/ROC-AUC/PR-AUC + band acc/macro-F1 + confusion; PR-AUC
selects under imbalance (~6% train water, ~24% test water).

## 13. Model Comparison
| Model | binF1 | ROC-AUC | PR-AUC | bandF1 |
|---|---|---|---|---|
| LogisticRegression | 0.631 | 0.875 | **0.749** | 0.472 |
| RandomForest | 0.430 | 0.755 | 0.393 | 0.357 |
| DecisionTree | 0.023 | 0.453 | 0.238 | 0.277 |
Selected **LogisticRegression** by PR-AUC. Multi-event training improved tree
transfer (RF spatial ROC 0.468→0.755) yet the linear model still won — reported,
not forced. Demo comparison unchanged in appendix.

## 14. Results
Held-out 14,204 points across 2 chips/events. Band confusion
(`real_confusion_LogisticRegression.png`), EDA (`real_*.png`), full table
(`real_model_comparison.csv`). India bands: LOW 21,556 / MEDIUM 2,535 /
HIGH 3,766 (n=27,857 cells).

## 15. India Flood Susceptibility Map
`outputs/maps/india_flood_risk_map.html` — whole-India default view
(center 22.5/79.5, zoom 5), LOW/MEDIUM/HIGH layers + rainfall + observed-chip
overlays, live-count legend, deterministic display stride (full data in CSV).
Titled "AI-Based Flood Susceptibility Map of India" with model-derived subtitle.

## 16. Dashboard
9 pages, REAL default, mode banners everywhere; Location Prediction = nearest
grid cell (approach B, documented). `python -m streamlit run dashboard/app.py`.

## 17. Testing
pytest: 10 demo + 12 real (schema/leakage/bands/split/artefacts) + 8 India
(boundary/mask/grid/predictions/map/no-S2-synthesis/demo-intact). All executed.

## 18. Limitations
10 m labels vs 0.5° rain; S2 pending `earthengine authenticate`; 2 events only;
reference-week national snapshot; fixed bands are display conveniences; coastal
slope median-imputation; susceptibility ≠ warning.

## 19. Future Scope
GEE auth → IMERG+S2 backfill (`scripts/gee_backfill_s2.py`) → retrain; more
Sen1Floods11 events; calibrated bands; SHAP; live feeds; cloud deploy.

## 20. Conclusion
Whole-India, model-derived susceptibility from real observations + real
environment, evaluated honestly, mapped interactively — with every limitation
documented and demo data never passed off as real.

## 21. References
Bonafilia et al. 2020 (Sen1Floods11); NASA GPM IMERG V07; NASA POWER; SRTM;
Copernicus Sentinel-2; GEE docs; GADM v4.1; scikit-learn/Folium/Streamlit/tifffile.

## Appendix A — Demo fallback (simulated, labelled)
1500 rows, rule score → qcut thirds; LogReg best (acc 0.767, F1 0.764).
Offline fallback only.
