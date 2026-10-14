"""Evaluation helpers (thin wrapper; training module does the heavy lifting)."""
import pandas as pd
from . import config


def load_comparison() -> pd.DataFrame:
    return pd.read_csv(config.COMPARISON_PATH)


def best_model_name() -> str:
    return load_comparison().iloc[0]["model"]
