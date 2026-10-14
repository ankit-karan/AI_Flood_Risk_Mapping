"""Exploratory Data Analysis: save PNG charts to outputs/plots/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from . import config

sns.set_theme(style="whitegrid")


def _save(fig, name: str):
    path = config.PLOTS_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return str(path)


def generate_eda_plots(df: pd.DataFrame) -> list:
    config.PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    order = [c for c in config.CLASSES if c in df["flood_risk"].unique()]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.histplot(df["rainfall"].dropna(), kde=True, ax=ax, color="steelblue")
    ax.set_title("Rainfall Distribution (mm)")
    made.append(_save(fig, "rainfall_dist.png"))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.histplot(df["elevation"].dropna(), kde=True, ax=ax, color="seagreen")
    ax.set_title("Elevation Distribution (m)")
    made.append(_save(fig, "elevation_dist.png"))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.countplot(x="flood_risk", data=df, order=order, hue="flood_risk",
                  palette={"LOW": "green", "MEDIUM": "orange", "HIGH": "red"},
                  legend=False, ax=ax)
    ax.set_title("Flood-Risk Class Distribution")
    made.append(_save(fig, "class_dist.png"))

    for col, title, fname in [
        ("rainfall", "Rainfall vs Flood Risk", "rainfall_vs_risk.png"),
        ("elevation", "Elevation vs Flood Risk", "elevation_vs_risk.png"),
        ("distance_to_water", "Distance to Water vs Flood Risk", "distance_vs_risk.png"),
    ]:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        sns.boxplot(x="flood_risk", y=col, data=df, order=order, hue="flood_risk",
                    palette={"LOW": "green", "MEDIUM": "orange", "HIGH": "red"},
                    legend=False, ax=ax)
        ax.set_title(title)
        made.append(_save(fig, fname))

    num_cols = [c for c in config.NUMERIC_FEATURES + ["susceptibility_score"]
                if c in df.columns]
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(df[num_cols].corr(numeric_only=True), annot=True, fmt=".2f",
                cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Heatmap (numeric features)")
    made.append(_save(fig, "correlation_heatmap.png"))
    return made


if __name__ == "__main__":
    from .data_preprocessing import load_and_prepare
    generate_eda_plots(load_and_prepare())
