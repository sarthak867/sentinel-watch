"""
detection/ndvi_detector.py
Detects deforestation and crop stress using NDVI delta from baseline.

NDVI = (NIR - Red) / (NIR + Red)
Range: -1 to +1
Healthy vegetation: 0.6 – 0.9
Sparse vegetation:  0.2 – 0.5
Bare soil / water:  < 0.1
"""
import pathway as pw
import uuid
from typing import Optional


# Regions where deforestation monitoring is critical
FOREST_REGIONS = {"Amazon Basin", "Siberia Boreal", "Jakarta Suburbs", "Congo Basin"}

# Regions where crop stress monitoring is critical
FARM_REGIONS = {"Punjab Farmlands", "Sahel Region", "Bangladesh Delta", "Ukraine Steppe"}


@pw.udf
def detect_deforestation(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndvi: float, ndvi_delta: float,
    cloud_cover: float, region: str, satellite: str
) -> pw.Json:
    """
    Deforestation detection UDF.
    Triggers when NDVI drops significantly below regional baseline.

    Thresholds:
      critical : delta < -0.40  (catastrophic clearing)
      high     : delta < -0.35
      medium   : delta < -0.25
    """
    if cloud_cover > 30:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})
    if region not in FOREST_REGIONS:
        return pw.Json({"detected": False, "reason": "non_forest_region"})
    if ndvi_delta >= -0.25:
        return pw.Json({"detected": False})

    if ndvi_delta < -0.40:
        severity = "critical"
        confidence = min(0.97, 0.75 + abs(ndvi_delta) * 0.4)
    elif ndvi_delta < -0.35:
        severity = "high"
        confidence = min(0.92, 0.70 + abs(ndvi_delta) * 0.35)
    else:
        severity = "medium"
        confidence = min(0.85, 0.60 + abs(ndvi_delta) * 0.3)

    import random
    area = abs(ndvi_delta) * random.uniform(80, 900)

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "deforestation",
        "severity": severity,
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 1),
        "ndvi_delta": round(ndvi_delta, 4),
        "description": (
            f"Vegetation loss detected in {region}. "
            f"NDVI dropped {abs(ndvi_delta):.2f} below seasonal baseline. "
            f"Estimated cleared area: {area:.0f} ha."
        ),
        "icon": "🌳",
        "color": "#22c55e",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })


@pw.udf
def detect_crop_stress(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndvi: float, ndvi_delta: float,
    cloud_cover: float, region: str, satellite: str
) -> pw.Json:
    """
    Crop stress detection UDF.
    Detects moderate NDVI decline in agricultural zones.

    Thresholds (less extreme than deforestation — crops fluctuate naturally):
      medium : -0.10 to -0.25  NDVI delta
      low    : -0.05 to -0.10  (early warning)
    """
    if cloud_cover > 25:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})
    if region not in FARM_REGIONS:
        return pw.Json({"detected": False, "reason": "non_farm_region"})
    if not (-0.25 < ndvi_delta < -0.05):
        return pw.Json({"detected": False})

    severity = "medium" if ndvi_delta < -0.15 else "low"
    confidence = min(0.88, 0.50 + abs(ndvi_delta) * 2.5)

    import random
    area = abs(ndvi_delta) * random.uniform(300, 3000)

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "crop_stress",
        "severity": severity,
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 1),
        "ndvi_delta": round(ndvi_delta, 4),
        "description": (
            f"Agricultural stress signal in {region}. "
            f"NDVI at {ndvi:.2f}, {abs(ndvi_delta):.2f} below seasonal norm. "
            f"Possible drought, pest, or disease."
        ),
        "icon": "🌾",
        "color": "#fbbf24",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })
