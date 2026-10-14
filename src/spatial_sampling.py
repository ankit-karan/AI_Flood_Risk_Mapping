"""Spatial sampling: chip grids + chip-based (spatial) train/test split.

Sampling: every SAMPLING_STRIDE-th pixel of each 512x512 LabelHand chip.
Nodata (-1) pixels are dropped; labels preserved as flooded 1/0.
Split: TRAIN_CHIPS vs TEST_CHIPS (different geographic chips) — no random
splitting of adjacent pixels, so no spatial leakage by construction.
"""
import numpy as np
import pandas as pd

from . import real_config as rc
from .sen1floods11_loader import read_label, pixel_to_lonlat


def sample_chip(chip_path, chip: str, stride: int = None) -> pd.DataFrame:
    stride = stride or rc.SAMPLING_STRIDE
    arr, geo = read_label(chip_path)
    rr = np.arange(0, arr.shape[0], stride)
    cc = np.arange(0, arr.shape[1], stride)
    rows, cols = np.meshgrid(rr, cc, indexing="ij")
    rows, cols = rows.ravel(), cols.ravel()
    vals = arr[rows, cols]
    keep = vals >= 0
    rows, cols, vals = rows[keep], cols[keep], vals[keep]
    lon, lat = pixel_to_lonlat(geo, rows, cols)
    return pd.DataFrame({"chip": chip, "row": rows, "col": cols,
                         "grow": rows // stride, "gcol": cols // stride,
                         "grid_h": len(rr), "grid_w": len(cc),
                         "longitude": np.round(lon, 6), "latitude": np.round(lat, 6),
                         "flooded": vals.astype(int)})


def spatial_split(df: pd.DataFrame):
    """Train/test split by chip (spatial). Returns (train, test)."""
    train = df[df["chip"].isin(rc.TRAIN_CHIPS)].reset_index(drop=True)
    test = df[df["chip"].isin(rc.TEST_CHIPS)].reset_index(drop=True)
    assert len(train) and len(test), "chip split produced an empty set"
    assert not set(train["chip"]).intersection(set(test["chip"])), "chip overlap = leakage"
    return train, test
