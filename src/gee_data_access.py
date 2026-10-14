"""Optional GEE Python access: detects availability, never breaks demo mode."""
from .utils import get_logger

logger = get_logger()


def gee_status() -> dict:
    """Return {'available': bool, 'reason': str}. No credentials are stored."""
    try:
        import ee  # earthengine-api (optional dependency)
    except ImportError:
        return {"available": False,
                "reason": "earthengine-api not installed (pip install earthengine-api)"}
    try:
        ee.Initialize()
        return {"available": True, "reason": "authenticated"}
    except Exception as e:
        return {"available": False,
                "reason": f"not authenticated — run `earthengine authenticate` ({e})".strip()}


def describe_collections() -> dict:
    return {
        "rainfall": "NASA/GPM_L3/IMERG_V07, band 'precipitation' (mm/hr), 0.1 deg",
        "terrain": "USGS/SRTMGL1_003, band 'elevation' (m), 30 m; slope via ee.Terrain.slope",
        "sentinel2": "COPERNICUS/S2_SR_HARMONIZED SR bands x10000; NDVI=(B8-B4)/(B8+B4), "
                     "NDWI=(B3-B8)/(B3+B8), NDBI=(B11-B8)/(B11+B8)",
    }
