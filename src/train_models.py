"""Train 3 classifiers on the same split; save best pipeline + comparison CSV."""
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, classification_report, confusion_matrix)

from . import config
from .data_preprocessing import get_preprocessor
from .utils import get_logger

logger = get_logger()

MODELS = {
    "LogisticRegression": LogisticRegression(max_iter=1000, random_state=config.RANDOM_STATE),
    "DecisionTree": DecisionTreeClassifier(random_state=config.RANDOM_STATE),
    "RandomForest": RandomForestClassifier(n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1),
}


def train_and_evaluate(X_train, X_test, y_train, y_test) -> pd.DataFrame:
    rows = []
    fitted = {}
    for name, clf in MODELS.items():
        pipe = Pipeline([("preprocess", get_preprocessor()), ("model", clf)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
        cv_acc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="accuracy").mean()
        rows.append({
            "model": name,
            "accuracy": round(accuracy_score(y_test, pred), 4),
            "precision_macro": round(precision_score(y_test, pred, average="macro", zero_division=0), 4),
            "recall_macro": round(recall_score(y_test, pred, average="macro", zero_division=0), 4),
            "f1_macro": round(f1_score(y_test, pred, average="macro", zero_division=0), 4),
            "cv_accuracy_5fold": round(float(cv_acc), 4),
        })
        fitted[name] = (pipe, pred)
        logger.info(f"{name}: acc={rows[-1]['accuracy']} f1={rows[-1]['f1_macro']}")
        logger.info(f"\n{classification_report(y_test, pred)}")
    comp = pd.DataFrame(rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)
    return comp, fitted


def save_best(comparison: pd.DataFrame, fitted: dict) -> str:
    best_name = comparison.iloc[0]["model"]
    best_pipe = fitted[best_name][0]
    joblib.dump(best_pipe, config.MODEL_PATH)
    comparison.to_csv(config.COMPARISON_PATH, index=False)
    logger.info(f"Best model: {best_name} -> {config.MODEL_PATH}")
    return best_name


def plot_confusion_matrices(fitted: dict, y_test) -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    paths = []
    for name, (_, pred) in fitted.items():
        cm = confusion_matrix(y_test, pred, labels=config.CLASSES)
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=config.CLASSES, yticklabels=config.CLASSES)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
        ax.set_title(f"Confusion Matrix — {name}")
        p = config.PLOTS_DIR / f"confusion_{name}.png"
        fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig)
        paths.append(str(p))
    return paths


def plot_feature_importance(pipe, feature_names_note: str = "") -> str | None:
    """Bar chart of RandomForest importances with expanded feature names."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        pre = pipe.named_steps["preprocess"]
        model = pipe.named_steps["model"]
        if not hasattr(model, "feature_importances_"):
            return None
        names = list(pre.get_feature_names_out())
        imp = np.asarray(model.feature_importances_)
        order = np.argsort(imp)[::-1][:15]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh([names[i] for i in order][::-1], imp[order][::-1], color="teal")
        ax.set_title("Feature Importance (Random Forest, top 15)")
        ax.set_xlabel("Importance")
        p = config.PLOTS_DIR / "feature_importance.png"
        fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig)
        return str(p)
    except Exception as e:
        logger.warning(f"feature importance plot skipped: {e}")
        return None
