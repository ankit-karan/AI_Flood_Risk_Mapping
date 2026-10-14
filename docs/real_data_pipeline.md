# Real-Data Pipeline — AI Flood Risk Mapping (primary mode)

## 1. Reference events (from ACTUAL Sen1Floods11 v1.1 STAC metadata)
- **Assam/Brahmaputra 2016-08-12** (event "India"): train `India_1072277`
  (water 8.6%, nodata 0%) + `India_981708` (4.0%, 14.5%); held-out test
  `India_591317` (43.5%, 6.1%, distant).
- **Sri-Lanka 2017-05-30** (126 chips surveyed, 4 sampled): train
  `Sri-Lanka_551926` (7.5%, 0%) + `Sri-Lanka_120804` (2.7%, 0%); held-out test
  `Sri-Lanka_233609` (2.6%, 1.9%).
- Catalog: `https://storage.googleapis.com/sen1floods11/v1.1/catalog/catalog.json`
  (public GCS, no key; only 6 label GeoTIFFs downloaded, ~6 KB each).

## 2. Temporal alignment (no future data)
- Flood references: 2016-08-12 (Assam), 2017-05-30 (Sri-Lanka, S1 date).
- Rainfall windows (per event, ending ON the date): 20160805–12 / 20170523–30.
- S2 reference windows: 2016-08-01→20 / 2017-05-15→06-15 (GEE; not retrieved).
- SRTM treated as time-invariant (documented assumption).

## 3. Sources & resolution
| Feature | Source | Unit | Native resolution |
|---|---|---|---|
| flooded | Sen1Floods11 LabelHand | 0/1 | 10 m |
| rainfall_sum/max | PRIMARY: GPM IMERG V07 accumulated (GEE); executed: NASA POWER daily | mm | 0.1° / ~0.5° |
| elevation/slope | SRTM (executed v3 points; GEE `USGS/SRTMGL1_003` + `ee.Terrain.slope`) | m / deg | 30 m |
| NDVI/NDWI/NDBI | `COPERNICUS/S2_SR_HARMONIZED` band math — **code-ready, NOT retrieved** | — | 10–20 m |
| boundary | GADM v4.1 India L0 | vector | — |

## 4. Sampling & split
- Every 6th pixel per 512×512 chip → 42,694 points (train 28,490 / test 14,204;
  train water 0.058, test water 0.241 — reported imbalance).
- Split **by chip AND event** (train 4 / test 2 incl. another event) — no
  adjacent-pixel split; `assert_no_leakage` enforced in code + tests.

## 5. Target & bands (two-stage, pre-declared)
Binary `flooded` → balanced classifiers → P(flood) → LOW (<0.33) / MEDIUM /
HIGH (>0.66); edges in `real_config.py` BEFORE training; no qcut.

## 6. Actual training results (spatial+event holdout)
| Model | binF1 | ROC-AUC | PR-AUC | bandF1 |
|---|---|---|---|---|
| LogisticRegression | 0.631 | 0.875 | **0.749** | 0.472 |
| RandomForest | 0.430 | 0.755 | 0.393 | 0.357 |
| DecisionTree | 0.023 | 0.453 | 0.238 | 0.277 |

Selected **LogisticRegression** (PR-AUC, imbalance-aware). Multi-event training
lifted tree transfer (RF spatial ROC 0.468→0.755) yet the linear model still won —
reported, not forced.

## 7. Whole-India prediction
0.1° (~11 km) GADM-masked lattice → 27,857 cells; real SRTM + POWER reference-week
features (same 5 as training); S2 empty-pending-backfill. Model → P(flood) →
bands → `india_flood_predictions.csv` (+observed chip-id or "Not available") →
`india_flood_risk_map.html` (whole-India default view, band/rain/observed layers).

## 8. Limitations
10 m labels vs 0.5° executed rain; S2 pending `earthengine authenticate`;
2 events only; reference-week national snapshot; fixed bands are display
conveniences; susceptibility ≠ warning. Land use via NDBI/NDVI path, drainage
via terrain proxies — no fabricated columns.
