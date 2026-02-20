"""
connectors/sentinel_feed.py
Pulls Sentinel-2 tiles from the Copernicus Data Space STAC API
and feeds them into Pathway as a streaming table.

Free API — no key needed for public datasets.
Docs: https://dataspace.copernicus.eu/analyse-and-process/apis/stac
"""
import pathway as pw
import requests
import json
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Generator
from ..schemas import SatelliteTileSchema


STAC_API = "https://catalogue.dataspace.copernicus.eu/stac/search"

# Bounding boxes for monitored regions [west, south, east, north]
REGION_BBOXES = {
    "Amazon Basin":     [-65.0, -5.0, -58.0,  0.0],
    "Bangladesh Delta": [ 88.0, 21.0,  93.0, 25.0],
    "Punjab Farmlands": [ 73.0, 28.0,  78.0, 33.0],
    "Jakarta Suburbs":  [106.0, -7.0, 108.0, -5.5],
    "Siberia Boreal":   [ 85.0, 57.0,  97.0, 64.0],
    "Sahel Region":     [ -2.0, 11.0,   7.0, 16.0],
}


def fetch_sentinel_tiles(
    region: str,
    bbox: list,
    days_back: int = 1,
    cloud_cover_max: int = 30
) -> list[dict]:
    """
    Query Copernicus STAC API for recent Sentinel-2 tiles.
    Returns list of tile metadata dicts.
    """
    end_dt   = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days_back)

    params = {
        "collections": ["SENTINEL-2"],
        "bbox": bbox,
        "datetime": f"{start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "limit": 20,
        "filter": f"eo:cloud_cover < {cloud_cover_max}",
    }

    try:
        resp = requests.post(STAC_API, json=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("features", [])
    except requests.RequestException as e:
        print(f"[Sentinel Feed] API error for {region}: {e}")
        return []

    tiles = []
    for item in items:
        props = item.get("properties", {})
        geometry = item.get("geometry", {})
        coords = geometry.get("coordinates", [[]])[0]
        if not coords:
            continue

        # Centroid approximation
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        lat = sum(lats) / len(lats)
        lon = sum(lons) / len(lons)

        # Extract or simulate spectral indices
        # In production: download actual band data via Assets API
        # and compute NDVI/NDWI from band arrays
        tiles.append({
            "tile_id": item.get("id", f"S2_{int(time.time()*1000)}"),
            "satellite": "Sentinel-2",
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "timestamp": int(time.time() * 1000),
            "ndvi": 0.0,      # → computed by band_processor.py
            "ndwi": 0.0,      # → computed by band_processor.py
            "band_swir": 0.0, # → computed by band_processor.py
            "cloud_cover": props.get("eo:cloud_cover", 0),
            "resolution_m": 10,
            "region": region,
        })
    return tiles


def sentinel_stream_generator(poll_interval: int = 300) -> Generator:
    """
    Generator that continuously polls Sentinel API and yields new tiles.
    poll_interval: seconds between API calls (default 5 min).
    """
    seen_ids = set()
    while True:
        for region, bbox in REGION_BBOXES.items():
            tiles = fetch_sentinel_tiles(region, bbox)
            for tile in tiles:
                if tile["tile_id"] not in seen_ids:
                    seen_ids.add(tile["tile_id"])
                    yield tile
        time.sleep(poll_interval)


def create_sentinel_pathway_table() -> pw.Table:
    """
    Create a Pathway streaming table from the Sentinel-2 feed.

    In hackathon mode: uses pw.io.python.read() with a generator.
    In production:     use pw.io.kafka.read() fed by a Kafka topic
                       that ingests Sentinel webhooks or SQS events.
    """

    class SentinelSubject(pw.io.python.ConnectorSubject):
        def run(self):
            for region, bbox in REGION_BBOXES.items():
                tiles = fetch_sentinel_tiles(region, bbox, days_back=2)
                for tile in tiles:
                    self.next(**tile)

    return pw.io.python.read(SentinelSubject(), schema=SatelliteTileSchema)
