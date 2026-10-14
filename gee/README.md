# GEE scripts — AI Flood Risk Mapping (real-data path)

These JavaScript snippets run in the [Google Earth Engine Code Editor](https://code.earthengine.google.com/).
They are the **primary, full-resolution** real-data path for the study area
declared in `src/real_config.py`:

- Event: Sen1Floods11 **India, 2016-08-12** (Assam/Brahmaputra valley)
- Rainfall window: **2016-08-05 → 2016-08-12** (NASA GPM IMERG V07 accumulated)
- Sentinel-2 window: **2016-08-01 → 2016-08-20** (COPERNICUS/S2_SR_HARMONIZED)
- Terrain: **USGS/SRTMGL1_003** elevation + `ee.Terrain.slope`

> Requires Earth Engine authentication (`earthengine authenticate`).
> The offline-capable pipeline in `scripts/run_real_pipeline.py` produces the
> same feature schema via direct NASA/SRTM/Sen1Floods11 downloads, so the
> project runs without GEE. GEE remains the reference for full-resolution
> Sentinel-2 indices (NDVI/NDWI/NDBI).

Files:

| File | Purpose |
|---|---|
| `rainfall.js` | GPM IMERG accumulated + max rainfall over the event window |
| `terrain.js` | SRTM elevation + slope |
| `sentinel_features.js` | Cloud-masked Sentinel-2 NDVI / NDWI / NDBI |
| `data_extraction.js` | Joins all layers, samples the study grid, previews |
| `india_grid.js` | Whole-India 0.1° lattice (mask to GADM/GAUL boundary in-editor) |
| `training_feature_extraction.js` | Per-chip IMERG+SRTM+S2 sampling, 6 chips, 2 events |
| `india_feature_extraction.js` | India-wide environmental stack (reference-week rain) |
| `export_features.js` | Exports the feature table to Google Drive (`REAL_FLOOD_FEATURES_India2016`) |

To use an export locally: download the CSV from Google Drive into `data/real/`
as `gee_export_features.csv` — `scripts/run_real_pipeline.py` will detect and
prefer it (see `src/real_config.py`) over the direct-download path.
