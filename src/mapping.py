"""Folium flood-risk map generation."""
import folium
from folium.plugins import MarkerCluster
import pandas as pd

from . import config
from .utils import get_logger

logger = get_logger()


def create_flood_map(df: pd.DataFrame, path=None, max_points: int = 500) -> str:
    path = path or config.MAP_PATH
    config.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    plot_df = df.dropna(subset=["latitude", "longitude"]).head(max_points)
    center = [float(plot_df["latitude"].mean()), float(plot_df["longitude"].mean())]
    m = folium.Map(location=center, zoom_start=6, tiles="OpenStreetMap")
    cluster = MarkerCluster().add_to(m)
    risk_col = "predicted_risk" if "predicted_risk" in plot_df.columns else "flood_risk"
    for _, r in plot_df.iterrows():
        risk = str(r.get(risk_col, "UNKNOWN"))
        color = config.RISK_COLORS.get(risk, "gray")
        popup = (f"<b>Risk: {risk}</b><br>"
                 f"Lat: {r['latitude']}, Lon: {r['longitude']}<br>"
                 f"Rainfall: {r.get('rainfall', '-')} mm<br>"
                 f"Elevation: {r.get('elevation', '-')} m<br>"
                 f"Slope: {r.get('slope', '-')} deg<br>"
                 f"Dist. to water: {r.get('distance_to_water', '-')} km<br>"
                 f"Drainage: {r.get('drainage_density', '-')} km/km2<br>"
                 f"Land use: {r.get('land_use', '-')}<br>"
                 f"Soil: {r.get('soil_type', '-')}<br>"
                 f"NDVI: {r.get('vegetation_index', '-')}")
        folium.CircleMarker(
            location=[r["latitude"], r["longitude"]], radius=5,
            color=color, fill=True, fillColor=color, fillOpacity=0.7,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{risk} risk").add_to(cluster)
    legend = """<div style="position:fixed;bottom:20px;left:20px;z-index:9999;
      background:white;padding:10px;border:2px solid grey;font-size:13px;">
      <b>Flood Risk (simulated demo data)</b><br>
      <span style="color:green;">&#9679;</span> LOW<br>
      <span style="color:orange;">&#9679;</span> MEDIUM<br>
      <span style="color:red;">&#9679;</span> HIGH</div>"""
    m.get_root().html.add_child(folium.Element(legend))
    m.save(str(path))
    logger.info(f"Map saved -> {path} ({len(plot_df)} points)")
    return str(path)
