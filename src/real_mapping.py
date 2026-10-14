"""Real-data Folium map: outputs/maps/real_flood_risk_map.html (never mixed with demo)."""
import folium
from folium.plugins import MarkerCluster
import pandas as pd

from . import real_config as rc
from .utils import get_logger

logger = get_logger()


def create_real_map(df: pd.DataFrame, path=None, max_points: int = 800) -> str:
    path = path or rc.REAL_MAP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    plot_df = df.dropna(subset=["latitude", "longitude"]).head(max_points)
    m = folium.Map(location=[float(plot_df["latitude"].mean()),
                             float(plot_df["longitude"].mean())],
                   zoom_start=11, tiles="OpenStreetMap")
    folium.map.Marker(
        location=[0, 0], icon=folium.DivIcon(html="")).add_to(m)  # keeps layer order stable
    cluster = MarkerCluster().add_to(m)
    colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    for _, r in plot_df.iterrows():
        band = str(r.get("susceptibility", r.get("flooded", "?")))
        band = {"1": "HIGH", "0": "LOW"}.get(band, band)
        color = colors.get(band, "gray")
        popup = (f"<b>Susceptibility: {band} (REAL DATA)</b><br>"
                 f"Lat: {r['latitude']:.5f}, Lon: {r['longitude']:.5f}<br>"
                 f"Rainfall 8-day sum: {r.get('rainfall_sum', '-')} mm<br>"
                 f"Rainfall max daily: {r.get('rainfall_max', '-')} mm<br>"
                 f"Elevation (SRTM): {r.get('elevation', '-')} m<br>"
                 f"Slope: {float(r.get('slope', 0)):.2f} deg<br>"
                 f"P(flood): {float(r.get('p_flood', float('nan'))):.3f}<br>"
                 f"Observed: {'flood' if r.get('flooded') == 1 else 'dry'} (Sen1Floods11)")
        folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=5,
                            color=color, fill=True, fillColor=color, fillOpacity=0.7,
                            popup=folium.Popup(popup, max_width=300),
                            tooltip=f"{band}").add_to(cluster)
    info = (f"<div style='position:fixed;bottom:20px;left:20px;z-index:9999;background:white;"
            f"padding:10px;border:2px solid grey;font-size:12px;'>"
            f"<b>REAL DATA — {rc.EVENT_NAME}</b><br>"
            f"<span style='color:green;'>&#9679;</span> LOW "
            f"<span style='color:orange;'>&#9679;</span> MEDIUM "
            f"<span style='color:red;'>&#9679;</span> HIGH<br>"
            f"Rain: NASA POWER 8-day to {rc.EVENT_DATE} | Elev: SRTM 30m | "
            f"Labels: Sen1Floods11</div>")
    m.get_root().html.add_child(folium.Element(info))
    m.save(str(path))
    logger.info(f"Real map saved -> {path} ({len(plot_df)} points)")
    return str(path)


def create_india_map(df: pd.DataFrame, path=None, max_points: int = 3000) -> str:
    """Whole-India susceptibility map (default view = entire India).

    30k+ markers would freeze browsers: a deterministic stride sample is drawn
    (documented on the map); the full per-cell file is india_flood_predictions.csv.
    """
    from . import real_config as rc
    path = path or rc.INDIA_MAP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    stride = max(1, len(df) // max_points)
    plot_df = df.iloc[::stride].reset_index(drop=True)
    m = folium.Map(location=list(rc.INDIA_CENTER), zoom_start=5, tiles="OpenStreetMap")
    colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    layers = {}
    for band in ["LOW", "MEDIUM", "HIGH"]:
        layers[band] = folium.FeatureGroup(name=f"Susceptibility {band}").add_to(m)
    rain_layer = folium.FeatureGroup(name="Rainfall (8-day mm)").add_to(m)
    obs = df[df["observed_flood"].astype(str).str.startswith("chip")]
    if len(obs):
        g = folium.FeatureGroup(name="Sen1Floods11 observed chips").add_to(m)
        for _, r in obs.drop_duplicates("observed_flood").iterrows():
            folium.Marker(location=[r["latitude"], r["longitude"]],
                          icon=folium.Icon(color="blue", icon="info-sign"),
                          popup=f"Observed reference: {r['observed_flood']}").add_to(g)
    for _, r in plot_df.iterrows():
        band = str(r["risk_class"])
        color = colors.get(band, "gray")
        obs_txt = r.get("observed_flood", "Not available for this location")
        popup = (f"<b>{band} susceptibility (MODEL PREDICTION)</b><br>"
                 f"Lat: {r['latitude']:.4f}, Lon: {r['longitude']:.4f}<br>"
                 f"Rainfall sum/mean/max: {r.get('rainfall_sum', '-')} / "
                 f"{r.get('rainfall_mean', '-')} / {r.get('rainfall_max', '-')} mm<br>"
                 f"Elevation: {r.get('elevation', '-')} m<br>"
                 f"Slope: {float(r.get('slope', 0)):.2f} deg<br>"
                 f"P(flood): {float(r.get('predicted_flood_probability', float('nan'))):.3f}<br>"
                 f"Observed flood: {obs_txt}")
        folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=3,
                            color=color, fill=True, fillColor=color, fillOpacity=0.6,
                            popup=folium.Popup(popup, max_width=300),
                            tooltip=f"{band}").add_to(layers.get(band, m))
    counts = df["risk_class"].value_counts()
    info = (f"<div style='position:fixed;bottom:20px;left:20px;z-index:9999;background:white;"
            f"padding:10px;border:2px solid grey;font-size:12px;'>"
            f"<b>AI-Based Flood Susceptibility Map of India</b><br>"
            f"Nationwide MODEL-DERIVED susceptibility (real environmental data).<br>"
            f"Flood observations exist only for labelled reference events.<br>"
            f"<span style='color:green;'>&#9679;</span> LOW ({counts.get('LOW', 0)}) "
            f"<span style='color:orange;'>&#9679;</span> MEDIUM ({counts.get('MEDIUM', 0)}) "
            f"<span style='color:red;'>&#9679;</span> HIGH ({counts.get('HIGH', 0)})<br>"
            f"Showing {len(plot_df)} of {len(df)} cells (stride {stride}).</div>")
    m.get_root().html.add_child(folium.Element(info))
    folium.LayerControl().add_to(m)
    m.save(str(path))
    logger.info(f"India map saved -> {path} ({len(plot_df)} of {len(df)} cells drawn)")
    return str(path)
