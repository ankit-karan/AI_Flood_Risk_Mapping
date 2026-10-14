"""Direct real-data clients (no GEE auth needed, honest source attribution).

- Elevation: SRTM v3 30m via OpenTopodata public API (no key).
  https://www.opentopodata.org/ — <=100 locations/request, ~1 call/s.
- Rainfall: NASA POWER daily PRECTOTCORR (bias-corrected precipitation, mm/day).
  https://power.larc.nasa.gov/ — keyless. NOTE: this is NASA POWER (MERRA-2/GEOS
  based, ~0.5 deg native), documented as such — NOT GPM IMERG, which needs GEE
  (see gee/rainfall.js for the primary IMERG path).

Both clients cache to data/real/cache/ and respect rate limits.
"""
import json
import time
import urllib.parse
import urllib.request

import numpy as np

from . import real_config as rc
from .utils import get_logger

logger = get_logger()
_LAST_CALL = {"t": 0.0}


def _polite_wait(min_gap: float = 1.1):
    dt = time.time() - _LAST_CALL["t"]
    if dt < min_gap:
        time.sleep(min_gap - dt)
    _LAST_CALL["t"] = time.time()


def _get_json(url: str, timeout: int = 45) -> dict:
    _polite_wait()
    req = urllib.request.Request(url, headers={"User-Agent": "AIML-PBL-student-project"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fetch_srtm_elevations(lats: np.ndarray, lons: np.ndarray,
                          cache_key: str) -> np.ndarray:
    """SRTM 30m elevation (m) for point arrays. Cached per cache_key."""
    cache = rc.CACHE_DIR / f"srtm_{cache_key}.json"
    if cache.exists():
        return np.array(json.loads(cache.read_text()), dtype=float)
    out = np.full(len(lats), np.nan)
    for i in range(0, len(lats), 100):
        chunk = [(float(lats[j]), float(lons[j])) for j in range(i, min(i + 100, len(lats)))]
        locs = "|".join(f"{la:.6f},{lo:.6f}" for la, lo in chunk)
        url = "https://api.opentopodata.org/v1/srtm30m?locations=" + urllib.parse.quote(locs, safe="|,.")
        try:
            res = _get_json(url).get("results", [])
            for k, r in enumerate(res):
                out[i + k] = float(r["elevation"]) if r.get("elevation") is not None else np.nan
        except Exception as e:
            logger.warning(f"SRTM chunk {i} failed: {e}")
    logger.info(f"SRTM: {np.isfinite(out).sum()}/{len(out)} elevations OK (chip {cache_key})")
    cache.write_text(json.dumps(out.tolist()))
    return out


def fetch_power_rain(lats: np.ndarray, lons: np.ndarray,
                     start: str, end: str, cache_key: str) -> tuple[np.ndarray, np.ndarray]:
    """Daily PRECTOTCORR (mm/day) -> per-point (sum, max) over [start, end]. Cached."""
    cache = rc.CACHE_DIR / f"power_{cache_key}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return np.array(d["sum"]), np.array(d["max"])
    sums = np.zeros(len(lats))
    maxs = np.zeros(len(lats))
    for i, (la, lo) in enumerate(zip(lats, lons)):
        q = (f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR"
             f"&community=AG&longitude={float(lo):.4f}&latitude={float(la):.4f}"
             f"&start={start}&end={end}&format=JSON")
        try:
            vals = list(_get_json(q)["properties"]["parameter"]["PRECTOTCORR"].values())
            vals = [float(v) for v in vals if v is not None and float(v) > -900]
            sums[i] = float(sum(vals))
            maxs[i] = float(max(vals)) if vals else 0.0
        except Exception as e:
            logger.warning(f"POWER point {i} failed: {e}")
    cache.write_text(json.dumps({"sum": sums.tolist(), "max": maxs.tolist()}))
    return sums, maxs
