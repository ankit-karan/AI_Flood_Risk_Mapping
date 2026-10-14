"""Feature engineering: small, explainable additions on top of raw GIS features."""
import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add runoff_index, lowland_index, drainage_proximity. Idempotent."""
    out = df.copy()
    if "runoff_index" not in out.columns and {"rainfall", "slope"}.issubset(out.columns):
        out["runoff_index"] = (out["rainfall"].fillna(out["rainfall"].median())
                               * (1 + out["slope"].fillna(0) / 35.0) / 1000.0)
    if "lowland_index" not in out.columns and {"rainfall", "elevation"}.issubset(out.columns):
        elev = out["elevation"].fillna(out["elevation"].median()).clip(lower=5)
        out["lowland_index"] = out["rainfall"].fillna(0) / elev
    if "drainage_proximity" not in out.columns and {"drainage_density", "distance_to_water"}.issubset(out.columns):
        out["drainage_proximity"] = (out["drainage_density"].fillna(0)
                                     / (1.0 + out["distance_to_water"].fillna(5)))
    return out


def describe_features() -> dict:
    return {
        "runoff_index": "rainfall scaled by slope (steeper -> faster runoff).",
        "lowland_index": "rainfall divided by elevation (low + wet -> risky).",
        "drainage_proximity": "drainage density discounted by distance to water.",
    }
