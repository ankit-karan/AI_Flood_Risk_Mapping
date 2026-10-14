from pathlib import Path
import pandas as pd
from src import config
from src.prediction import predict_single, predict_dataframe
from src.mapping import create_flood_map

SAMPLE = {
    "latitude": 19.0, "longitude": 73.5, "rainfall": 2200,
    "elevation": 60, "slope": 3.0, "distance_to_water": 0.8,
    "drainage_density": 3.5, "land_use": "Wetland",
    "soil_type": "Clay", "vegetation_index": 0.3,
}


def test_prediction_valid_class():
    assert predict_single(SAMPLE) in {"LOW", "MEDIUM", "HIGH"}


def test_batch_prediction():
    df = pd.DataFrame([SAMPLE, {**SAMPLE, "rainfall": 500,
        "elevation": 900, "land_use": "Forest", "soil_type": "Sand"}])
    out = predict_dataframe(df)
    assert list(out) and set(out) <= {"LOW", "MEDIUM", "HIGH"}


def test_map_generation(tmp_path):
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    if "predicted_risk" not in df.columns:
        df["predicted_risk"] = df["flood_risk"]
    p = create_flood_map(df.head(30), path=tmp_path / "m.html", max_points=30)
    html = Path(p).read_text(encoding="utf-8")
    assert "Flood Risk" in html and "LOW" in html
