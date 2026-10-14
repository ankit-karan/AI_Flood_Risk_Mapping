"""Real model pipeline: binary flood -> P(flood) -> pre-declared LOW/MED/HIGH bands.

Two-stage method (documented, §9 of the upgrade spec):
  1. Binary classifier trained on Sen1Floods11 flooded (1/0), class_weight balanced.
  2. P(flood) mapped through PRE-DECLARED equal-width bands (BAND_EDGES in
     real_config, set before training): P<0.33 LOW, 0.33–0.66 MEDIUM, >0.66 HIGH.
No qcut, no tuning of bands to force equal counts.

Metrics: binary acc/prec/rec/F1/ROC-AUC/PR-AUC + 3-class acc/macro-F1/confusion.
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score, confusion_matrix)

from . import real_config as rc
from .real_data_preprocessing import get_real_preprocessor, assert_no_leakage
from .utils import get_logger

logger = get_logger()

MODELS = {
    "LogisticRegression": LogisticRegression(max_iter=2000, class_weight="balanced",
                                            random_state=rc.RANDOM_STATE),
    "DecisionTree": DecisionTreeClassifier(class_weight="balanced",
                                          random_state=rc.RANDOM_STATE),
    "RandomForest": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                           n_jobs=-1, random_state=rc.RANDOM_STATE),
}
CLASSES3 = ["LOW", "MEDIUM", "HIGH"]


def band_proba(proba: np.ndarray) -> np.ndarray:
    lo, hi = rc.BAND_EDGES
    return np.where(proba < lo, "LOW", np.where(proba > hi, "HIGH", "MEDIUM"))


def band_truth(y01: np.ndarray) -> np.ndarray:
    """Reference bands for evaluation: flooded=HIGH, dry=LOW (MEDIUM unused in truth)."""
    return np.where(np.asarray(y01) == 1, "HIGH", "LOW")


def train_real(X_train: pd.DataFrame, y_train: pd.Series,
               X_test: pd.DataFrame, y_test: pd.Series):
    assert_no_leakage(list(X_train.columns))
    rows, fitted, proba_test = [], {}, {}
    for name, clf in MODELS.items():
        pipe = Pipeline([("preprocess", get_real_preprocessor()), ("model", clf)])
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        pred01 = (proba >= 0.5).astype(int)
        bands = band_proba(proba)
        rows.append({
            "model": name,
            "bin_accuracy": round(accuracy_score(y_test, pred01), 4),
            "bin_precision": round(precision_score(y_test, pred01, zero_division=0), 4),
            "bin_recall": round(recall_score(y_test, pred01, zero_division=0), 4),
            "bin_f1": round(f1_score(y_test, pred01, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, proba), 4),
            "pr_auc": round(average_precision_score(y_test, proba), 4),
            "band_accuracy": round(accuracy_score(band_truth(y_test), bands), 4),
            "band_f1_macro": round(f1_score(band_truth(y_test), bands,
                                           labels=CLASSES3, average="macro",
                                           zero_division=0), 4),
        })
        fitted[name] = pipe
        proba_test[name] = proba
        logger.info(f"{name}: binF1={rows[-1]['bin_f1']} PR-AUC={rows[-1]['pr_auc']} "
                    f"bandF1={rows[-1]['band_f1_macro']}")
    comp = pd.DataFrame(rows).sort_values("pr_auc", ascending=False).reset_index(drop=True)
    return comp, fitted, proba_test


def save_best_real(comp: pd.DataFrame, fitted: dict) -> str:
    best = comp.iloc[0]["model"]  # PR-AUC primary (imbalanced flood detection)
    joblib.dump(fitted[best], rc.REAL_MODEL_PATH)
    comp.to_csv(rc.REAL_COMPARISON_PATH, index=False)
    logger.info(f"Best real model: {best} -> {rc.REAL_MODEL_PATH}")
    return best


def real_confusion_bands(y_test, proba) -> np.ndarray:
    return confusion_matrix(band_truth(y_test), band_proba(proba), labels=CLASSES3)


def predict_real_single(rainfall_sum: float, rainfall_max: float,
                        elevation: float, slope: float) -> tuple[str, float]:
    """Classify one real location. Returns (band, P(flood))."""
    import joblib
    model = joblib.load(rc.REAL_MODEL_PATH)
    row = pd.DataFrame([{"rainfall_sum": rainfall_sum, "rainfall_max": rainfall_max,
                         "elevation": elevation, "slope": slope,
                         "lowland_index": rainfall_sum / max(float(elevation), 1.0)}])
    p = float(model.predict_proba(row)[0, 1])
    return str(band_proba(np.array([p]))[0]), p
