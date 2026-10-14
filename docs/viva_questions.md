# Viva Questions — AI Flood Risk Mapping (95 Q&A, simple language)

## Part A — Demo/fallback pipeline (Q1–50, unchanged)

1. **What is flood-risk mapping?** Dividing areas into LOW/MEDIUM/HIGH flood
   susceptibility so planners can see which places need attention.
2. **What is your project title/code?** AI Flood Risk Mapping, B12-FAIR-AI-12.
3. **What is the official goal?** Create a basic flood-risk classification map.
4. **What is GIS?** Geographic Information Systems — storing and showing data
   linked to locations (latitude/longitude) on maps.
5. **What is machine learning?** Learning patterns from data so the computer can
   classify new unseen places.
6. **Why classification, not regression?** We need categories (LOW/MEDIUM/HIGH)
   for a readable map, not an exact water depth number.
7. **Why three classes?** Simple for users and reports; more classes would need
   much more data to be reliable.
8. **What is rainfall, and why does it matter?** Yearly rain in mm; more rain
   means more water that can flood. Highest weight (0.30) in our score.
9. **Why does elevation matter?** Water flows downhill; low areas collect water.
10. **Why does distance-to-water matter?** Places near rivers/lakes overflow first.
11. **What is drainage density?** Total stream length per km²; dense networks move
    flood water into an area quickly.
12. **What is slope?** Steepness in degrees; flat land ponds, steep land drains
    (but causes fast runoff downhill).
13. **What is land use?** How land is used (Urban/Forest/...); concrete cities
    shed water, forests absorb it.
14. **What is soil type?** Clay holds water (risky), sand drains fast (safer).
15. **What is vegetation index (NDVI)?** 0–1 greenness from satellites; plants slow
    runoff, so low NDVI slightly raises risk.
16. **Is your data real?** No — simulated/demo data with logical rules, clearly
    labelled as prototype data.
17. **How are labels created?** Weighted score from normalised factors, then
    `pd.qcut` into thirds → LOW/MEDIUM/HIGH.
18. **What is preprocessing?** Cleaning data (duplicates, invalid coords, missing
    values) before training.
19. **How are missing values handled?** Median imputation (numbers),
    most-frequent (categories), inside the pipeline.
20. **What is normalisation/scaling?** Putting numbers on the same scale
    (StandardScaler) so big units like rainfall don't dominate wrongly.
21. **What is encoding?** Converting text (Urban, Clay) to numbers with OneHot
    encoding so models can use them.
22. **What is train-test split?** 80% to learn, 20% unseen to test honestly.
    Stratified keeps class balance; `random_state=42` makes it reproducible.
23. **What is data leakage?** Test info accidentally used in training; avoided by
    fitting imputers/scalers only on train data (Pipeline).
24. **What is overfitting?** Memorising training data but failing on new data;
    checked with test set + 5-fold cross-validation.
25. **What is cross-validation?** Splitting train data into 5 parts, training 5
    times and averaging accuracy — a stability check.
26. **What is Logistic Regression?** A linear classifier that draws straight
    boundaries between classes; simple baseline.
27. **What is a Decision Tree?** If-else rules learned from data (e.g. if
    rainfall > 2000 and elevation < 100 → HIGH); easy to explain.
28. **What is Random Forest?** Many trees trained on random data/feature subsets,
    voting together — handles non-linear patterns, usually most accurate.
29. **Why compare 3 models?** To show trade-offs, not assume one is best.
30. **Which model won?** Check `outputs/reports/model_comparison.csv` — the best
    model is the one with the highest macro-F1 (in our run: LogisticRegression).
    The winner is decided by the numbers, never assumed beforehand.
31. **Why F1, not just accuracy?** Accuracy hides class-wise failures; macro-F1
    averages all three classes fairly.
32. **What is precision?** Of places we called HIGH, how many truly were HIGH.
33. **What is recall?** Of all truly-HIGH places, how many did we catch.
34. **What is F1-score?** Harmonic mean of precision and recall — balances both.
35. **What is a confusion matrix?** Table of actual vs predicted classes showing
    exactly where the model confuses MEDIUM with HIGH, etc.
36. **What is feature importance?** Which inputs the forest relied on most
    (rainfall/elevation usually top); shown in `feature_importance.png`.
37. **What is SHAP?** Optional per-prediction explanations; excluded here to keep
    installation simple on student laptops.
38. **What is Folium?** Python library making interactive Leaflet maps (HTML)
    with zoom, markers and popups.
39. **What is Streamlit?** Python framework turning scripts into a web dashboard
    (our 7 pages: Home…About).
40. **What is SRTM?** NASA's Shuttle Radar Topography Mission — free global
    elevation data we could plug in as real `elevation`.
41. **What is Sentinel/Landsat?** European/US satellites giving imagery for NDVI
    and land-use mapping.
42. **What is remote sensing?** Measuring earth from satellites/aircraft without
    touching it (rainfall, elevation, imagery).
43. **What is Sen1Floods11?** Public labelled Sentinel-1 flood dataset usable as
    real training labels in future work.
44. **What is Google Earth Engine?** Cloud platform for processing satellite data
    at scale (alternative data source).
45. **What does clicking a map point show?** Lat/lon, rainfall, elevation, slope,
    distance-to-water, drainage, predicted risk.
46. **How do I run the project?** `python -m venv venv`, activate,
    `pip install -r requirements.txt`, `python scripts/run_pipeline.py`,
    `streamlit run dashboard/app.py`.
47. **Where is the trained model?** `models/flood_risk_model.pkl` (full pipeline
    with preprocessing, loaded by `src/prediction.py`).
48. **What are the limitations?** Simulated data; small region; no real-time
    warnings; coarse features; needs real validation before any real use.
49. **Why is this NOT an operational warning system?** No live rain/river feeds,
    no calibration against real floods, coarse demo resolution.
50. **Future scope?** Real NASA/SRTM/Sentinel feeds, live rainfall APIs,
    deep learning on imagery, SHAP explainability, cloud deployment.

## Part B — Real-data pipeline (Q51–75)
51. **Why did you choose NASA GPM / POWER rainfall?** Rain immediately before a
    flood is its main driver; we used 8-day accumulation + max daily rain ending
    on the event date. IMERG (GEE) is the primary path; NASA POWER ran offline.
52. **What is IMERG?** NASA's merged satellite rainfall product (mm/hr, 0.1°);
    our `gee/rainfall.js` accumulates it over 2016-08-05→12.
53. **What is SRTM / DEM?** NASA's 30 m global elevation model; a DEM (digital
    elevation model) stores ground height per pixel — our `elevation`.
54. **How did you calculate slope?** Central differences on the SRTM grid
    converted to metres (same concept as `ee.Terrain.slope`), in degrees.
55. **Why use Sentinel-2?** Free 10 m optical imagery for surface wetness/greenness
    (NDVI/NDWI/NDBI). Ours is GEE-reference only — monsoon clouds + auth blocked
    retrieval, honestly documented.
56. **What is NDVI / NDWI / NDBI?** (NIR−Red)/(NIR+Red) greenness;
    (Green−NIR)/(Green+NIR) water; (SWIR−NIR)/(SWIR+NIR) built-up. Pure band math
    in `src/real_feature_engineering.py`.
57. **What is Sen1Floods11?** 4,831 hand-labelled Sentinel-1 flood chips in 11
    events (Bonafilia et al. 2020); we used 3 India 2016-08-12 chips (20,645 pts).
58. **Why Google Earth Engine?** It hosts IMERG/SRTM/Sentinel-2 together so joins
    happen in the cloud; our `gee/` scripts do rainfall, terrain, indices, export.
59. **How did you align datasets?** Common chip bboxes (EPSG:4326) + event-locked
    windows; 0.5° POWER rain nearest-assigned to 10 m label grid (documented
    mismatch); manifest records every source/resolution.
60. **What is spatial resolution?** Smallest pixel/object a dataset sees (labels
    10 m, SRTM 30 m, POWER ~0.5°) — mixing them is a stated limitation.
61. **What is spatial leakage?** Neighbouring pixels leaking between train/test;
    avoided by splitting whole chips (train 2 chips, test 1 distant chip).
62. **What is temporal leakage?** Using post-event data as input; avoided — rain
    window ends ON the event date, terrain is time-invariant by assumption.
63. **What is the target variable?** Binary `flooded` (Sen1Floods11 1/0), then
    P(flood) banded to LOW/MEDIUM/HIGH — never a fabricated score.
64. **Why LOW/MEDIUM/HIGH?** Readable map classes from pre-declared equal-width
    probability bands (0.33/0.66), set before training, not qcut-tuned.
65. **Prediction vs susceptibility?** We estimate relative susceptibility
    (where is riskier), never when a flood will occur — no warning claim.
66. **Why might accuracy be misleading?** ~20% water: always-dry scores 80%;
    hence PR-AUC + F1, class weights, and reported (not hidden) imbalance.
67. **Why PR-AUC / macro F1?** PR-AUC is primary for imbalanced flood detection;
    macro-F1 fairly averages the three display bands.
68. **Which model won and why?** LogisticRegression (PR-AUC 0.884, ROC 0.874);
    trees memorised chip-specific cuts (RF spatial ROC 0.468 vs 0.877 random-split
    diagnostic) while the linear trend transferred — an honest spatial lesson.
69. **How big is the real result?** 20,645 points; test chip 6,947; map
    `outputs/maps/real_flood_risk_map.html`; manifest `data/real/data_manifest.json`.
70. **What manual setup remains?** `earthengine authenticate` for the GEE path
    (IMERG + Sentinel-2 at full resolution); direct-download path already runs.
71. **Why Assam 2016?** Real Sen1Floods11 India event with dated labels overlapping
    retrievable POWER/SRTM coverage — chosen from metadata, not assumed.
72. **Where is the real model?** `models/real_flood_model.pkl` (full pipeline).
73. **Real-data limitations?** Resolution mismatch, no S2 indices yet, one event
    only, crude fixed bands, no live feeds.
74. **Demo vs real in the dashboard?** Sidebar mode selector; every page banners
    its mode — synthetic never shown as real.
75. **One-line project summary?** Real flood observations + real rain/terrain
    classify Assam locations into relative susceptibility on an interactive map —
    an academic prototype, not a warning system.

## Part C — Whole-India final system (Q76–95)
76. **Why NASA GPM / what is IMERG?** Primary rainfall: 0.1° merged satellite
    product; accumulated per event window in `gee/rainfall.js`. POWER ran offline
    as the documented substitute.
77. **Why SRTM / what is DEM / slope?** 30 m global elevation model; slope =
    central differences on the DEM (ee.Terrain.slope concept), in degrees.
78. **Why Sentinel-2 / NDVI / NDWI / NDBI?** 10 m optical bands; pure band math
    (B8/B4/B3/B11). Code-complete in GEE; retrieval needs one auth command —
    never synthesised, columns stay empty until then.
79. **Why Sen1Floods11 / what is a flood mask?** Real hand-labelled flood pixels
    (1 = water, 0 = land) for dated events — our training/reference truth.
80. **Observation vs susceptibility?** Sen1Floods11 = observed reference (chips
    only); model output = predicted probability; India map = model-derived
    susceptibility. Never called "actual flood map".
81. **Why LOW/MEDIUM/HIGH?** Pre-declared equal-width P(flood) bands (0.33/0.66)
    — display classes, not tuned counts, no qcut.
82. **Spatial / temporal leakage?** Chip-level holdout (train 4 chips, test 2 incl.
    another event); rain windows end ON each event date.
83. **Why a grid / why whole India?** Goal is a national map; 0.1° (~11 km)
    GADM-masked lattice honestly matches coarse rain input.
84. **Why aren't all areas ground truth?** Labels exist only inside 6 chips;
    everywhere else shows predictions + "Observed: Not available".
85. **What is model probability?** Calibrated-ish likelihood of flood given the
    five real features — drives bands and popups.
86. **Feature consistency?** Identical 5 features train ↔ predict; S2 excluded
    from both until retrieved.
87. **Which model / metrics?** LogisticRegression by PR-AUC (see manifest);
    binary + band metrics reported, never accuracy alone.
88. **Prediction approach in dashboard?** Nearest India grid cell (approach B) —
    documented on the page.
89. **Land use / drainage?** Via NDBI/NDVI path and terrain proxies; no invented
    land_use/soil/drainage columns.
90. **GEE's exact role?** Primary remote-sensing layer (filter/clip/reduce/sample/
    export); `gee/` has 8 scripts; auth: `earthengine authenticate`.
91. **What if GEE auth is missing?** Direct-download path runs; S2 stays empty;
    backfill script stops with instructions — nothing faked.
92. **Map layers / popups?** Band layers + rainfall + observed chips, LayerControl;
    popups: lat/lon, rain, elev, slope, indices (when available), P, band, observed.
93. **Limitations?** Resolution mismatch, 2 events, reference-week rain, fixed bands,
    no live feeds — susceptibility only.
94. **What remains manual?** `earthengine authenticate` → S2/IMERG backfill → retrain.
95. **Final one-liner?** Real observed floods + real environment → evaluated model →
    whole-India susceptibility map + dashboard; honest, reproducible, faculty-ready.
