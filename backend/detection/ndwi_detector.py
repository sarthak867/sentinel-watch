"""
detection/ndwi_detector.py
Detects flood propagation using NDWI delta from seasonal baseline.

NDWI = (Green - NIR) / (Green + NIR)
Range: -1 to +1
Water bodies:    > 0.3
Moist soil:      0.0 – 0.3
Dry / vegetated: < 0.0

Flood = sudden spike in NDWI above seasonal norm for that region.
"""
import pathway as pw
import uuid


# Flood-prone regions
FLOOD_REGIONS = {
    "Bangladesh Delta", "Amazon Basin", "Mekong Delta",
    "Indus Plains", "Nile Delta", "Mississippi Floodplain"
}


@pw.udf
def detect_flood(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndwi: float, ndwi_delta: float,
    cloud_cover: float, region: str, satellite: str
) -> pw.Json:
    """
    Flood detection UDF.
    Triggers when NDWI rises significantly above seasonal baseline.

    Thresholds:
      critical : delta > 0.50  (major inundation)
      high     : delta > 0.35
      medium   : delta > 0.25
    """
    if cloud_cover > 35:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})
    if ndwi_delta <= 0.25:
        return pw.Json({"detected": False})

    if ndwi_delta > 0.50:
        severity = "critical"
        confidence = min(0.98, 0.80 + ndwi_delta * 0.25)
    elif ndwi_delta > 0.35:
        severity = "high"
        confidence = min(0.93, 0.72 + ndwi_delta * 0.20)
    else:
        severity = "medium"
        confidence = min(0.85, 0.65 + ndwi_delta * 0.15)

    import random
    # Flood area scales strongly with NDWI delta
    area = ndwi_delta * random.uniform(500, 8000)

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "flood",
        "severity": severity,
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 1),
        "ndwi_delta": round(ndwi_delta, 4),
        "description": (
            f"Flood propagation detected in {region}. "
            f"Water extent expanded: NDWI +{ndwi_delta:.2f} above seasonal norm. "
            f"Estimated inundated area: {area:.0f} ha."
        ),
        "icon": "🌊",
        "color": "#38bdf8",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })


@pw.udf
def detect_drought_water_loss(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndwi: float, ndwi_delta: float,
    cloud_cover: float, region: str, satellite: str
) -> pw.Json:
    """
    Inverse: detect significant water body shrinkage (drought / reservoir depletion).
    Triggers on strong negative NDWI delta in water-bearing regions.
    """
    if cloud_cover > 30:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})
    if ndwi_delta >= -0.30:
        return pw.Json({"detected": False})

    import random
    area = abs(ndwi_delta) * random.uniform(200, 3000)
    confidence = min(0.90, 0.60 + abs(ndwi_delta) * 0.5)

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "drought",
        "severity": "high" if ndwi_delta < -0.45 else "medium",
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 1),
        "ndwi_delta": round(ndwi_delta, 4),
        "description": (
            f"Water body shrinkage in {region}. "
            f"NDWI dropped {abs(ndwi_delta):.2f} — possible drought or reservoir depletion."
        ),
        "icon": "🏜️",
        "color": "#f59e0b",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })
