"""Real feature engineering — every feature from a real source, no invention.

- slope: finite-difference slope (degrees) from the SRTM elevation grid,
  same concept as ee.Terrain.slope. Computed ONLY from elevation (an input),
  never from the flood label.
- lowland_index: rainfall_sum / max(elevation, 1) — wetter + lower = riskier.
- NDVI/NDWI/NDBI band-math helpers are implemented for real Sentinel-2 SR
  bands (B8, B4, B3, B11) so GEE exports (gee/) plug in directly; they are
  NOT computed from random data and are absent until real S2 is available.
"""
import numpy as np
import pandas as pd


def slope_from_points(elev: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                      grows: np.ndarray, gcols: np.ndarray, shape: tuple) -> np.ndarray:
    """Slope in degrees via central differences on the per-chip elevation grid.

    grows/gcols are grid indices (not pixel indices); shape is the full grid
    shape. Pixel size (m) is inferred from the actual coordinate span, so no
    hardcoded resolution is assumed.
    """
    grid = np.full(shape, np.nan)
    grid[grows, gcols] = elev
    fill = float(np.nanmean(grid))
    full = np.where(np.isnan(grid), fill, grid)  # SRTM voids are rare on floodplains
    step_lat = abs(float(lats.max() - lats.min())) / max(1, shape[0] - 1) or 1e-9
    step_lon = abs(float(lons.max() - lons.min())) / max(1, shape[1] - 1) or 1e-9
    lat0 = float(np.mean(lats))
    m_per_lat = 111320.0
    m_per_lon = 111320.0 * max(0.2, abs(float(np.cos(np.radians(lat0)))))
    dz_drow, dz_dcol = np.gradient(full)
    grad = np.sqrt((dz_dcol / (step_lon * m_per_lon)) ** 2
                   + (dz_drow / (step_lat * m_per_lat)) ** 2)
    return np.degrees(np.arctan(grad))[grows, gcols]


def add_lowland_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["lowland_index"] = out["rainfall_sum"] / out["elevation"].clip(lower=1.0)
    return out


# --- Real Sentinel-2 band math (used only with genuine S2 surface reflectance) ---
def ndvi(nir_B8: np.ndarray, red_B4: np.ndarray) -> np.ndarray:
    return (nir_B8 - red_B4) / np.clip(nir_B8 + red_B4, 1e-6, None)


def ndwi(green_B3: np.ndarray, nir_B8: np.ndarray) -> np.ndarray:
    return (green_B3 - nir_B8) / np.clip(green_B3 + nir_B8, 1e-6, None)


def ndbi(swir_B11: np.ndarray, nir_B8: np.ndarray) -> np.ndarray:
    return (swir_B11 - nir_B8) / np.clip(swir_B11 + nir_B8, 1e-6, None)
