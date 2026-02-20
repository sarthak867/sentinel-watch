"""
pathway_engine.py — Main Pathway streaming pipeline orchestrator

Wires together:
  Satellite feeds → Detection UDFs → Knowledge Graph → Alerts + API
"""
import pathway as pw
import json
import time
import random
import threading

from backend.schemas import SatelliteTileSchema
from backend.knowledge_graph.region_baseline import (
    get_baseline, compute_ndvi_delta, compute_ndwi_delta
)
from backend.alerts.websocket_server import start_websocket_server, push_event
from backend.alerts.alert_router import route_alert
from backend.api.rest_server import start_rest_server, update_events, update_tiles, update_stats


# ─── Simulated tile feed (hackathon mode) ─────────────────────────
# Replace with:
#   from backend.connectors import create_sentinel_pathway_table
#   from backend.connectors import create_merged_satellite_table (Kafka)

REGIONS = [
    "Amazon Basin", "Bangladesh Delta", "Punjab Farmlands",
    "Jakarta Suburbs", "Siberia Boreal", "Sahel Region",
]

NDVI_BASELINE = {r: get_baseline(r)["ndvi"] for r in REGIONS}
NDWI_BASELINE = {r: get_baseline(r)["ndwi"] for r in REGIONS}


def generate_mock_tiles(n: int = 80) -> list:
    tiles = []
    for i in range(n):
        region  = random.choice(REGIONS)
        anomaly = random.random() < 0.28
        b_ndvi  = NDVI_BASELINE[region]
        b_ndwi  = NDWI_BASELINE[region]

        ndvi = b_ndvi + random.uniform(-0.05, 0.05)
        ndwi = b_ndwi + random.uniform(-0.03, 0.03)
        swir = random.uniform(0.1, 0.4)

        if anomaly:
            event_type = random.choice(["deforestation", "flood", "fire", "crop_stress", "construction"])
            if event_type == "deforestation":
                ndvi -= random.uniform(0.25, 0.55)
            elif event_type == "flood":
                ndwi += random.uniform(0.28, 0.65)
            elif event_type == "fire":
                swir = random.uniform(0.76, 0.95)
                ndvi = random.uniform(-0.1, 0.08)
            elif event_type == "crop_stress":
                ndvi -= random.uniform(0.10, 0.22)
            elif event_type == "construction":
                ndvi -= random.uniform(0.15, 0.35)
                swir = random.uniform(0.56, 0.72)

        tiles.append({
            "tile_id":     f"TILE_{region.replace(' ','_')}_{i:04d}",
            "satellite":   random.choice(["Sentinel-2", "Landsat-8"]),
            "lat":         round(get_baseline(region).get("lat", 0) + random.uniform(-0.5, 0.5), 4),
            "lon":         round(get_baseline(region).get("lon", 0) + random.uniform(-0.5, 0.5), 4),
            "timestamp":   int(time.time() * 1000) - random.randint(0, 3_600_000),
            "ndvi":        round(max(-1.0, min(1.0, ndvi)), 4),
            "ndwi":        round(max(-1.0, min(1.0, ndwi)), 4),
            "band_swir":   round(max(0.0, min(1.0, swir)), 4),
            "cloud_cover": round(random.uniform(0, 20), 1),
            "resolution_m":random.choice([10, 20, 30]),
            "region":      region,
        })
    return tiles


# ─── Core detection UDF ───────────────────────────────────────────
@pw.udf
def detect_all_events(
    tile_id: str, satellite: str, lat: float, lon: float,
    timestamp: int, ndvi: float, ndwi: float, band_swir: float,
    cloud_cover: float, resolution_m: int, region: str,
) -> pw.Json:
    """
    Master change detection UDF — runs spectral analysis on every tile.
    Combines NDVI, NDWI, and SWIR signals.
    """
    if cloud_cover > 30:
        return pw.Json({"detected": False})

    from backend.knowledge_graph.region_baseline import compute_ndvi_delta, compute_ndwi_delta
    import uuid

    ndvi_delta = compute_ndvi_delta(ndvi, region)
    ndwi_delta = compute_ndwi_delta(ndwi, region)
    detected   = []

    # 1. Deforestation
    if ndvi_delta < -0.25 and region in {"Amazon Basin", "Siberia Boreal", "Jakarta Suburbs", "Congo Basin"}:
        sev  = "critical" if ndvi_delta < -0.40 else "high" if ndvi_delta < -0.35 else "medium"
        conf = min(0.97, 0.65 + abs(ndvi_delta))
        detected.append({"event_type": "deforestation", "severity": sev, "confidence": conf,
                          "area_hectares": abs(ndvi_delta) * random.uniform(80, 900),
                          "ndvi_delta": ndvi_delta, "icon": "🌳", "color": "#22c55e",
                          "description": f"Vegetation loss: NDVI Δ={ndvi_delta:.2f}"})

    # 2. Flood
    if ndwi_delta > 0.25:
        sev  = "critical" if ndwi_delta > 0.50 else "high" if ndwi_delta > 0.35 else "medium"
        conf = min(0.98, 0.70 + ndwi_delta * 0.4)
        detected.append({"event_type": "flood", "severity": sev, "confidence": conf,
                          "area_hectares": ndwi_delta * random.uniform(500, 8000),
                          "ndvi_delta": ndvi_delta, "icon": "🌊", "color": "#38bdf8",
                          "description": f"Inundation: NDWI Δ=+{ndwi_delta:.2f}"})

    # 3. Fire
    if band_swir > 0.75 and ndvi < 0.10:
        sev  = "critical" if band_swir > 0.85 else "high"
        conf = min(0.97, 0.70 + band_swir * 0.30)
        detected.append({"event_type": "fire", "severity": sev, "confidence": conf,
                          "area_hectares": band_swir * random.uniform(200, 5000),
                          "ndvi_delta": ndvi_delta, "icon": "🔥", "color": "#fb923c",
                          "description": f"Fire/burn: SWIR={band_swir:.2f}, NDVI={ndvi:.2f}"})

    # 4. Crop stress
    if -0.25 < ndvi_delta < -0.10 and region in {"Punjab Farmlands", "Sahel Region", "Bangladesh Delta"}:
        detected.append({"event_type": "crop_stress", "severity": "medium",
                          "confidence": min(0.85, 0.55 + abs(ndvi_delta) * 2.5),
                          "area_hectares": abs(ndvi_delta) * random.uniform(300, 3000),
                          "ndvi_delta": ndvi_delta, "icon": "🌾", "color": "#fbbf24",
                          "description": f"Crop stress: NDVI Δ={ndvi_delta:.2f}"})

    # 5. Construction
    if ndvi_delta < -0.15 and band_swir > 0.55 and ndvi < 0.30:
        detected.append({"event_type": "construction", "severity": "medium",
                          "confidence": min(0.84, 0.50 + abs(ndvi_delta) * 0.8),
                          "area_hectares": abs(ndvi_delta) * random.uniform(2, 50),
                          "ndvi_delta": ndvi_delta, "icon": "🏗️", "color": "#a78bfa",
                          "description": f"Built-up area: NDVI Δ={ndvi_delta:.2f}, SWIR={band_swir:.2f}"})

    if not detected:
        return pw.Json({"detected": False})

    sev_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    top = max(detected, key=lambda e: sev_rank.get(e["severity"], 0))

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "tile_id": tile_id, "satellite": satellite,
        "lat": lat, "lon": lon, "timestamp": timestamp, "region": region,
        **top,
    })


# ─── Build & run the pipeline ─────────────────────────────────────
def run_pipeline():
    tiles_data = generate_mock_tiles(100)

    table = pw.debug.table_from_rows(
        schema=SatelliteTileSchema,
        rows=[(
            d["tile_id"], d["satellite"], d["lat"], d["lon"],
            d["timestamp"], d["ndvi"], d["ndwi"], d["band_swir"],
            d["cloud_cover"], d["resolution_m"], d["region"]
        ) for d in tiles_data]
    )

    with_detections = table.select(
        *pw.this,
        detection=detect_all_events(
            pw.this.tile_id, pw.this.satellite, pw.this.lat, pw.this.lon,
            pw.this.timestamp, pw.this.ndvi, pw.this.ndwi, pw.this.band_swir,
            pw.this.cloud_cover, pw.this.resolution_m, pw.this.region,
        )
    )

    pw.debug.compute_and_print(with_detections, n_rows=5)

    # Push to API and WebSocket
    update_tiles(tiles_data)
    events = [dict(d, **{"detected": True}) for d in tiles_data
              if random.random() < 0.3]  # simulate detected subset

    update_events(events)
    for e in events[:5]:
        push_event(e)


if __name__ == "__main__":
    print("=" * 60)
    print("  SENTINEL//WATCH — Pathway Stream Engine")
    print("=" * 60)

    start_rest_server(port=8765)
    start_websocket_server(port=8766)

    print("\n[Pipeline] Running change detection...\n")
    run_pipeline()

    print("\n[Ready] Services running:")
    print("  REST API   → http://localhost:8765")
    print("  WebSocket  → ws://localhost:8766")
    print("  Dashboard  → open frontend/public/index.html\n")

    # Keep alive
    try:
        while True:
            time.sleep(5)
            # Simulate new tiles arriving
            new_tiles = generate_mock_tiles(5)
            update_tiles(new_tiles)
            update_stats(
                rate=round(random.uniform(8, 15), 1),
                latency_ms=random.randint(120, 340)
            )
    except KeyboardInterrupt:
        print("\n[Stop] Pipeline shut down.")
