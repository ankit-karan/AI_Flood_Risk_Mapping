"""Whole-India prediction grid: GADM boundary + 0.1° masked lattice.

Boundary: GADM v4.1 India level-0 (authoritative public boundary), cached to
data/real/cache/india_boundary.geojson on first fetch. Point-in-polygon is a
vectorised ray-casting implementation (no shapely needed); the polygon is
decimated (same source, tiny precision loss irrelevant at ~11 km cells).
"""
import json
import urllib.request

import numpy as np
import pandas as pd

from . import real_config as rc
from .utils import get_logger

logger = get_logger()


def fetch_boundary() -> dict:
    """Fetch (once) and cache the GADM India boundary."""
    if not rc.INDIA_BOUNDARY_CACHE.exists():
        req = urllib.request.Request(rc.INDIA_BOUNDARY_URL,
                                     headers={"User-Agent": "AIML-PBL-student-project"})
        with urllib.request.urlopen(req, timeout=120) as r:
            rc.INDIA_BOUNDARY_CACHE.write_bytes(r.read())
        logger.info(f"India boundary cached -> {rc.INDIA_BOUNDARY_CACHE}")
    return json.loads(rc.INDIA_BOUNDARY_CACHE.read_text())


def _rings(geom: dict) -> list:
    """Outer rings of a Polygon/MultiPolygon geometry as (N,2) arrays."""
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    else:
        polys = geom["coordinates"]
    rings = []
    for poly in polys:
        for ring in poly:
            a = np.asarray(ring, dtype=float)
            if len(a) > 3:
                rings.append(a)
    return rings


def _decimate(ring: np.ndarray, tol: float = 0.01) -> np.ndarray:
    """Radial-distance decimation (keeps shape, drops redundant vertices)."""
    keep = [0]
    ax, ay = ring[0]
    for i in range(1, len(ring)):
        if abs(ring[i][0] - ax) + abs(ring[i][1] - ay) > tol:
            keep.append(i)
            ax, ay = ring[i]
    if keep[-1] != len(ring) - 1:
        keep.append(len(ring) - 1)
    return ring[np.array(keep)]


def points_in_india(lons: np.ndarray, lats: np.ndarray, rings: list) -> np.ndarray:
    """Even-odd ray casting, ring by ring, bbox-prefiltered and chunked.

    Only points inside a ring's bbox are tested against it, in small chunks,
    so memory stays flat regardless of ring size.
    """
    inside = np.zeros(len(lons), dtype=bool)
    for ring in rings:
        x, y = ring[:, 0], ring[:, 1]
        xmin, xmax, ymin, ymax = x.min(), x.max(), y.min(), y.max()
        cand = np.nonzero((lons >= xmin) & (lons <= xmax) &
                          (lats >= ymin) & (lats <= ymax))[0]
        if len(cand) == 0:
            continue
        x1, y1 = x[:-1], y[:-1]
        x2, y2 = x[1:], y[1:]
        crossings = np.zeros(len(cand), dtype=np.int32)
        for a in range(0, len(cand), 4000):
            b = cand[a:a + 4000]
            la = lats[b][:, None]
            cond = ((y1 > la) != (y2 > la))
            with np.errstate(divide="ignore", invalid="ignore"):
                xinters = (x2 - x1) * (la - y1) / (y2 - y1 + 1e-12) + x1
            crossings[a:a + 4000] = (cond & (lons[b][:, None] < xinters)).sum(axis=1)
        inside[cand] ^= (crossings % 2 == 1)
    return inside


def build_india_grid() -> pd.DataFrame:
    """0.1° lattice over the India bbox, masked to the GADM boundary."""
    gj = fetch_boundary()
    rings = [_decimate(r) for f in gj["features"] for r in _rings(f["geometry"])]
    logger.info(f"Boundary rings: {len(rings)}, vertices: {sum(len(r) for r in rings)}")
    lon0, lon1 = rc.GRID_LON
    lat0, lat1 = rc.GRID_LAT
    step = rc.GRID_STEP_DEG
    glon, glat = np.meshgrid(np.arange(lon0, lon1 + 1e-9, step),
                             np.arange(lat0, lat1 + 1e-9, step))
    lons, lats = glon.ravel(), glat.ravel()
    mask = points_in_india(lons, lats, rings)
    df = pd.DataFrame({"grid_id": np.arange(mask.sum()),
                       "longitude": np.round(lons[mask], 4),
                       "latitude": np.round(lats[mask], 4)})
    logger.info(f"India grid: {len(df)} land cells at {step}° (~{step * 111:.0f} km)")
    return df
