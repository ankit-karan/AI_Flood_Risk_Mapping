"""Real-data preprocessing: cleaning + leakage guard + numeric transformer."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import real_config as rc
from .utils import get_logger

logger = get_logger()

# Columns that must NEVER appear as model inputs (label or label-derived).
FORBIDDEN_FEATURES = {"flooded", "flood_risk", "susceptibility_score", "LabelHand", "water"}


def assert_no_leakage(feature_cols: list):
    bad = set(feature_cols) & FORBIDDEN_FEATURES
    if bad:
        raise ValueError(f"TARGET LEAKAGE: label-derived columns as features: {bad}")


def clean_real(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().drop_duplicates(subset=["chip", "row", "col"])
    out = out[out["flooded"].isin([0, 1])]  # safety: only binary labels
    out = out[out["latitude"].between(-90, 90) & out["longitude"].between(-180, 180)]
    for c in rc.REAL_NUMERIC:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.reset_index(drop=True)


def get_real_preprocessor() -> ColumnTransformer:
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")),
                         ("scaler", StandardScaler())])
    return ColumnTransformer([("num", num_pipe, rc.REAL_NUMERIC)])
