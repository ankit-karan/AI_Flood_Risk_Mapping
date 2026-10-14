from pathlib import Path
import pandas as pd
from src import config
from src.data_generation import generate_synthetic_data
from src.data_preprocessing import clean_data, split_data
from src.train_models import train_and_evaluate


def test_model_training():
    df = clean_data(generate_synthetic_data(n=400, seed=3))
    X_train, X_test, y_train, y_test = split_data(df)
    comp, fitted = train_and_evaluate(X_train, X_test, y_train, y_test)
    assert set(comp["model"]) == {"LogisticRegression", "DecisionTree", "RandomForest"}
    assert (comp["f1_macro"] > 0.5).all()
    assert (comp["accuracy"] > 0.5).all()


def test_model_file_exists_after_pipeline():
    # Only valid after scripts/run_pipeline.py has run
    assert config.MODEL_PATH.exists(), "Run python scripts/run_pipeline.py first"


def test_comparison_file_exists():
    assert config.COMPARISON_PATH.exists(), "Run python scripts/run_pipeline.py first"
