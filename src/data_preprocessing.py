"""Preprocessing: cleaning + sklearn ColumnTransformer + train/test split."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config
from .feature_engineering import add_features
from .utils import get_logger

logger = get_logger()


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicates, fix invalid coords, coerce numerics. Keeps NaNs for imputers."""
    out = df.copy()
    before = len(out)
    out = out.drop_duplicates()
    # Valid ranges (rows outside are data errors -> drop)
    out = out[(out["latitude"].between( -90, 90)) & (out["longitude"].between(-180, 180))]
    for col in config.NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["vegetation_index"] = out["vegetation_index"].clip(0, 1)
    out = add_features(out)
    logger.info(f"clean_data: {before} -> {len(out)} rows "
                f"({before - len(out)} duplicates/invalid removed)")
    return out


def get_preprocessor() -> ColumnTransformer:
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, config.ALL_NUMERIC),
        ("cat", categorical_pipe, config.CATEGORICAL_FEATURES),
    ])


def split_data(df: pd.DataFrame, test_size: float = None, seed: int = None):
    test_size = test_size or config.TEST_SIZE
    seed = config.RANDOM_STATE if seed is None else seed
    X = df[[c for c in config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES
            + config.ENGINEERED_FEATURES if c in df.columns]]
    y = df[config.TARGET_COL]
    return train_test_split(X, y, test_size=test_size,
                            random_state=seed, stratify=y)


def load_and_prepare(path=None) -> pd.DataFrame:
    from .utils import ensure_sample_data
    df = pd.read_csv(path) if path else ensure_sample_data()
    df = clean_data(df)
    df.to_csv(config.PROCESSED_DATA_PATH, index=False)
    return df
