# Dataset

## REAL DATA (primary) — training/reference
`data/real/real_features.csv` — labelled points from 6 Sen1Floods11 chips
(Assam 2016: 1072277/981708 train, 591317 test; Sri-Lanka 2017: 551926/120804
train, 233609 test). Per-chip event-locked NASA POWER rainfall windows
(20160805–12 / 20170523–30); SRTM elevation + derived slope; lowland_index.
Target `flooded` (0/1 preserved observations). Manifest: `data_manifest.json`.

## REAL DATA (primary) — whole-India prediction grid
`data/real/india_grid_features.csv` — 0.1° (~11 km) GADM-masked lattice
(~27.9k cells): `grid_id, latitude, longitude, rainfall_sum/mean/max
(reference week), elevation, slope, NDVI/NDWI/NDBI (empty until GEE backfill),
lowland_index`. `data/real/india_flood_predictions.csv` adds
`predicted_flood_probability, risk_class, observed_flood` (chip id or
"Not available for this location").

## PRIMARY vs EXECUTED sources
PRIMARY rainfall: NASA GPM IMERG V07 accumulated per event window (GEE,
`gee/rainfall.js`, `gee/training_feature_extraction.js`). Executed offline
substitute with identical schema: NASA POWER PRECTOTCORR (clearly labelled).
PRIMARY S2 indices: COPERNICUS/S2_SR_HARMONIZED NDVI/NDWI/NDBI (GEE,
`gee/sentinel_features.js`); NOT retrieved — columns stay empty, model does
not use them. Terrain: SRTM (executed SRTM-v3 point queries; GEE
`USGS/SRTMGL1_003` reference).

## DEMO DATA (fallback, clearly labelled) — simulated
`data/sample/flood_data_sample.csv` — 1500 rows, seed 42, qcut thirds.
**Simulated/demo dataset for academic prototyping — never real measurements.**
