"""Synthetic (simulated/demo) flood-susceptibility dataset generator.

ACADEMIC DISCLAIMER: this is NOT measured real-world data. It is a
rule-based simulation so the project runs without external GIS downloads.
Logical relationships are deliberate:
  higher rainfall + lower elevation + flatter slope + nearer to water +
  higher drainage density + less vegetation + clay/wetland  -> higher risk.
"""
import numpy as np
import pandas as pd

from . import config
from .utils import get_logger

logger = get_logger()

LAND_USES = ["Agriculture", "Urban", "Forest", "Wetland", "Barren"]
LAND_USE_P = [0.35, 0.25, 0.20, 0.10, 0.10]
SOILS = ["Clay", "Loam", "Silt", "Sand"]
SOIL_P = [0.30, 0.30, 0.20, 0.20]

LAND_BONUS = {"Wetland": 0.15, "Urban": 0.08, "Agriculture": 0.05,
              "Barren": 0.02, "Forest": -0.05}
SOIL_BONUS = {"Clay": 0.08, "Silt": 0.03, "Loam": 0.0, "Sand": -0.05}


def generate_synthetic_data(n: int = 1500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lat = rng.uniform(18.0, 28.0, n)          # central-India-like window
    lon = rng.uniform(72.0, 80.0, n)
    rainfall = np.clip(rng.normal(1400, 600, n), 300, 3500)
    elevation = np.clip(rng.exponential(250, n) + rng.uniform(0, 300, n), 5, 1200)
    slope = np.clip(elevation / 1200 * 25 + rng.normal(0, 3, n), 0, 35)
    distance_to_water = np.clip(rng.exponential(4.0, n), 0.05, 20.0)
    drainage_density = np.clip(rng.normal(2.2, 0.9, n), 0.3, 5.0)
    land_use = rng.choice(LAND_USES, size=n, p=LAND_USE_P)
    soil_type = rng.choice(SOILS, size=n, p=SOIL_P)
    # NDVI: forests green, urban/barren sparse
    ndvi_base = rng.normal(0.45, 0.18, n)
    ndvi_base += np.where(land_use == "Forest", 0.25,
                 np.where(land_use == "Urban", -0.18,
                 np.where(land_use == "Barren", -0.12,
                 np.where(land_use == "Wetland", 0.05, 0.0))))
    vegetation_index = np.clip(ndvi_base, 0.05, 0.95)

    # --- susceptibility score in ~[0, 1] ---
    n_rain = (rainfall - 300) / (3500 - 300)
    n_lowelev = 1.0 - (elevation - 5) / (1200 - 5)
    n_flatslope = 1.0 - slope / 35.0
    n_nearwater = 1.0 - distance_to_water / 20.0
    n_drain = (drainage_density - 0.3) / (5.0 - 0.3)
    n_bare = 1.0 - vegetation_index
    lb = np.array([LAND_BONUS[v] for v in land_use])
    sb = np.array([SOIL_BONUS[v] for v in soil_type])
    score = (0.30 * n_rain + 0.22 * n_lowelev + 0.10 * n_flatslope
             + 0.15 * n_nearwater + 0.12 * n_drain + 0.05 * n_bare
             + lb + sb + rng.normal(0, 0.05, n))
    score = np.clip(score, 0, 1)

    # Quantile labels -> roughly balanced LOW/MEDIUM/HIGH (reproducible)
    labels = pd.qcut(score, q=3, labels=["LOW", "MEDIUM", "HIGH"]).astype(str)

    df = pd.DataFrame({
        "latitude": np.round(lat, 4),
        "longitude": np.round(lon, 4),
        "rainfall": np.round(rainfall, 1),
        "elevation": np.round(elevation, 1),
        "slope": np.round(slope, 2),
        "distance_to_water": np.round(distance_to_water, 2),
        "drainage_density": np.round(drainage_density, 2),
        "land_use": land_use,
        "soil_type": soil_type,
        "vegetation_index": np.round(vegetation_index, 3),
        "susceptibility_score": np.round(score, 4),
        "flood_risk": labels,
    })

    # Inject ~1.5% missing values to exercise the preprocessing pipeline
    for col in ["rainfall", "elevation", "vegetation_index"]:
        idx = rng.choice(n, size=max(1, n // 70), replace=False)
        df.loc[idx, col] = np.nan
    idx = rng.choice(n, size=max(1, n // 100), replace=False)
    df.loc[idx, "soil_type"] = np.nan
    return df


def generate_and_save(n: int = None, seed: int = None) -> pd.DataFrame:
    n = n or config.N_SAMPLES
    seed = config.RANDOM_STATE if seed is None else seed
    df = generate_synthetic_data(n=n, seed=seed)
    config.DATA_SAMPLE.mkdir(parents=True, exist_ok=True)
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.SAMPLE_DATA_PATH, index=False)
    df.to_csv(config.DATA_RAW / "flood_data_raw.csv", index=False)
    logger.info(f"Saved {len(df)} simulated rows -> {config.SAMPLE_DATA_PATH}")
    logger.info(f"Class balance:\n{df['flood_risk'].value_counts()}")
    return df


if __name__ == "__main__":
    generate_and_save()
