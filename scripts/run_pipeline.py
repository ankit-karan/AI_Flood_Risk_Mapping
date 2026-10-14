"""End-to-end pipeline: data -> EDA -> train -> map -> reports. Idempotent."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from src.utils import get_logger
from src.data_generation import generate_and_save
from src.data_preprocessing import load_and_prepare, split_data
from src.eda import generate_eda_plots
from src.train_models import (train_and_evaluate, save_best,
                              plot_confusion_matrices, plot_feature_importance)
from src.prediction import predict_dataframe
from src.mapping import create_flood_map

logger = get_logger()


def main():
    logger.info("=== AI Flood Risk Mapping pipeline (simulated demo data) ===")
    df = generate_and_save()                       # 1. data
    df = load_and_prepare()                        # 2-3. clean + processed save
    plots = generate_eda_plots(df)                 # 4. EDA
    logger.info(f"EDA plots: {len(plots)} saved")
    X_train, X_test, y_train, y_test = split_data(df)  # 5. split
    comp, fitted = train_and_evaluate(X_train, X_test, y_train, y_test)  # 6.
    best = save_best(comp, fitted)                 # 7-8. save best
    plot_confusion_matrices(fitted, y_test)
    # Always show RF importances (interpretability requirement),
    # even when another model wins on F1.
    if "RandomForest" in fitted:
        plot_feature_importance(fitted["RandomForest"][0])
    df["predicted_risk"] = predict_dataframe(df)   # 9. predictions
    create_flood_map(df)                           # 10. map
    logger.info("=== Pipeline complete ===")
    logger.info(f"Best model: {best}\n{comp.to_string(index=False)}")
    logger.info(f"Model: {config.MODEL_PATH} | Map: {config.MAP_PATH}")


if __name__ == "__main__":
    main()
