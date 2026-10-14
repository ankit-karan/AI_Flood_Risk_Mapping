"""Sen1Floods11 access: STAC catalog -> chip label GeoTIFF -> numpy mask.

Real flood observations. Label semantics (v1.1 LabelHand, int16):
  -1 = nodata (dropped), 0 = land/non-flood, 1 = water/flood.
Target column 'flooded' preserves this binary observation (1/0) untouched.
"""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
import tifffile

from . import real_config as rc


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "AIML-PBL-student-project"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def list_india_items() -> list:
    """Return STAC item hrefs for India hand-labelled chips (proves catalog access)."""
    col = json.loads(_get(rc.STAC_COLLECTION_URL).decode())
    return [l["href"] for l in col.get("links", [])
            if l.get("rel") == "item" and "/India_" in l.get("href", "")]


def download_label(chip: str, dest_dir: Path | None = None) -> Path:
    """Download one chip's LabelHand GeoTIFF (few KB). Returns local path."""
    dest_dir = Path(dest_dir or rc.CACHE_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{chip}_LabelHand.tif"
    if not dest.exists():
        url = rc.GCS_TIF_TEMPLATE.format(chip=chip)
        dest.write_bytes(_get(url))
    return dest


def read_label(path: Path) -> tuple[np.ndarray, dict]:
    """Read mask + georeferencing.

    Georeferencing is derived from the chip's STAC bbox (lon_min..lon_max /
    lat_min..lat_max over the 512x512 chip) — no fragile TIFF-tag parsing.
    """
    name = Path(path).stem.replace("_LabelHand", "")
    arr = tifffile.imread(str(path))
    bbox = rc.CHIP_BBOX[name]  # [minlon, minlat, maxlon, maxlat]
    geo = {"lon0": float(bbox[0]), "lat0": float(bbox[3]),   # top-left corner
           "dx": (float(bbox[2]) - float(bbox[0])) / arr.shape[1],
           "dy": (float(bbox[3]) - float(bbox[1])) / arr.shape[0]}
    return np.asarray(arr), geo


def pixel_to_lonlat(geo: dict, rows: np.ndarray, cols: np.ndarray):
    lon = geo["lon0"] + (cols + 0.5) * geo["dx"]
    lat = geo["lat0"] - (rows + 0.5) * geo["dy"]   # tiepoint is top-left
    return lon, lat


def label_stats(arr: np.ndarray) -> dict:
    n = int(arr.size)
    return {"pixels": n,
            "nodata_frac": round(float((arr == -1).sum()) / n, 4),
            "water_frac": round(float((arr == 1).sum()) / n, 4)}
