"""
connectors/landsat_feed.py
Pulls Landsat-8/9 tiles from USGS EarthExplorer M2M API.

Requires free USGS account:
  Register at: https://ers.cr.usgs.gov/register
  API docs:    https://m2m.cr.usgs.gov/api/docs/json/

Landsat-8 has 30m resolution (vs Sentinel-2's 10m),
but provides longer historical archive and global coverage.
"""
import pathway as pw
import requests
import json
import time
import os
from datetime import datetime, timedelta, timezone
from ..schemas import SatelliteTileSchema


M2M_API   = "https://m2m.cr.usgs.gov/api/api/json/stable"
USGS_USER = os.getenv("USGS_USERNAME", "")
USGS_PASS = os.getenv("USGS_PASSWORD", "")

# Landsat dataset IDs
DATASETS = {
    "landsat_c2l2": "landsat_ot_c2_l2",   # Landsat 8/9 Collection 2 Level-2
}

REGION_BBOXES = {
    "Amazon Basin":     {"west": -65.0, "south": -5.0, "east": -58.0, "north":  0.0},
    "Bangladesh Delta": {"west":  88.0, "south": 21.0, "east":  93.0, "north": 25.0},
    "Punjab Farmlands": {"west":  73.0, "south": 28.0, "east":  78.0, "north": 33.0},
    "Jakarta Suburbs":  {"west": 106.0, "south": -7.0, "east": 108.0, "north": -5.5},
    "Siberia Boreal":   {"west":  85.0, "south": 57.0, "east":  97.0, "north": 64.0},
    "Sahel Region":     {"west":  -2.0, "south": 11.0, "east":   7.0, "north": 16.0},
}


class USGSAuth:
    """Handles USGS M2M API authentication with token caching."""

    def __init__(self):
        self._token = None
        self._token_ts = 0

    def get_token(self) -> str:
        if self._token and (time.time() - self._token_ts) < 3600:
            return self._token
        resp = requests.post(
            f"{M2M_API}/login",
            json={"username": USGS_USER, "password": USGS_PASS},
            timeout=15
        )
        resp.raise_for_status()
        self._token = resp.json()["data"]
        self._token_ts = time.time()
        return self._token


_auth = USGSAuth()


def fetch_landsat_tiles(region: str, bbox: dict, days_back: int = 3) -> list[dict]:
    """
    Search USGS M2M API for recent Landsat-8/9 scenes.
    """
    if not USGS_USER:
        print("[Landsat Feed] USGS_USERNAME not set — skipping")
        return []

    end_dt   = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days_back)

    try:
        token = _auth.get_token()
        headers = {"X-Auth-Token": token}

        payload = {
            "datasetName": DATASETS["landsat_c2l2"],
            "spatialFilter": {
                "filterType": "mbr",
                "lowerLeft":  {"latitude": bbox["south"], "longitude": bbox["west"]},
                "upperRight": {"latitude": bbox["north"], "longitude": bbox["east"]},
            },
            "temporalFilter": {
                "start": start_dt.strftime("%Y-%m-%d"),
                "end":   end_dt.strftime("%Y-%m-%d"),
            },
            "maxResults": 10,
            "startingNumber": 1,
        }

        resp = requests.post(f"{M2M_API}/scene-search", json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        scenes = resp.json().get("data", {}).get("results", [])

    except Exception as e:
        print(f"[Landsat Feed] Error fetching {region}: {e}")
        return []

    tiles = []
    for scene in scenes:
        spatial = scene.get("spatialCoverage", {}).get("coordinates", [[]])[0]
        if not spatial:
            continue
        lons = [c[0] for c in spatial]
        lats = [c[1] for c in spatial]

        tiles.append({
            "tile_id": scene.get("entityId", f"L8_{int(time.time()*1000)}"),
            "satellite": "Landsat-8",
            "lat": round(sum(lats) / len(lats), 4),
            "lon": round(sum(lons) / len(lons), 4),
            "timestamp": int(time.time() * 1000),
            "ndvi": 0.0,       # computed from downloaded bands
            "ndwi": 0.0,
            "band_swir": 0.0,
            "cloud_cover": scene.get("cloudCover", 0),
            "resolution_m": 30,
            "region": region,
        })
    return tiles


def create_landsat_pathway_table() -> pw.Table:
    """Create Pathway streaming table from Landsat feed."""

    class LandsatSubject(pw.io.python.ConnectorSubject):
        def run(self):
            for region, bbox in REGION_BBOXES.items():
                tiles = fetch_landsat_tiles(region, bbox)
                for tile in tiles:
                    self.next(**tile)

    return pw.io.python.read(LandsatSubject(), schema=SatelliteTileSchema)
