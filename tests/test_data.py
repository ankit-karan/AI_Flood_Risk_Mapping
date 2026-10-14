import pandas as pd
from src.data_generation import generate_synthetic_data


def test_generation_shape_and_classes():
    df = generate_synthetic_data(n=300, seed=0)
    assert len(df) == 300
    assert set(df["flood_risk"].unique()) <= {"LOW", "MEDIUM", "HIGH"}
    assert set(df["flood_risk"].unique()) == {"LOW", "MEDIUM", "HIGH"}


def test_logic_high_rain_low_elev_riskier():
    """Wet lowlands should average higher susceptibility than dry highlands."""
    df = generate_synthetic_data(n=600, seed=1).dropna(subset=["susceptibility_score"])
    wet_low = df[(df["rainfall"] > 1800) & (df["elevation"] < 150)]
    dry_high = df[(df["rainfall"] < 900) & (df["elevation"] > 600)]
    assert len(wet_low) > 5 and len(dry_high) > 5
    assert wet_low["susceptibility_score"].mean() > dry_high["susceptibility_score"].mean()
