"""Inference: load saved pipeline, predict single records or DataFrames."""
import joblib
import pandas as pd

from . import config
from .feature_engineering import add_features


def load_model(path=None):
    path = path or config.MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run: python scripts/run_pipeline.py")
    return joblib.load(path)


def predict_single(features: dict, path=None) -> str:
    """features: dict with the 10 input fields. Returns LOW/MEDIUM/HIGH."""
    model = load_model(path)
    df = pd.DataFrame([features])
    df = add_features(df)
    pred = model.predict(df)[0]
    return str(pred)


def predict_dataframe(df: pd.DataFrame, path=None) -> pd.Series:
    model = load_model(path)
    df2 = add_features(df.copy())
    return pd.Series(model.predict(df2), index=df.index, name="predicted_risk")


if __name__ == "__main__":
    print(predict_single({
        "latitude": 19.0, "longitude": 73.5, "rainfall": 2200,
        "elevation": 60, "slope": 3.0, "distance_to_water": 0.8,
        "drainage_density": 3.5, "land_use": "Wetland",
        "soil_type": "Clay", "vegetation_index": 0.3}))
