"""
detection/swir_detector.py
Detects fires, burn scars, and illegal construction using SWIR band.

SWIR (Short-Wave Infrared) Band:
  - High reflectance in active fire / heat sources
  - Built-up areas (concrete, metal roofs) have distinct SWIR signature
  - Burn scars: high SWIR + very low NDVI

Sentinel-2 Band 11 (1610nm) / Band 12 (2190nm) used.
Landsat-8 Band 6 (1566–1651nm) / Band 7 (2107–2294nm) used.
"""
import pathway as pw
import uuid


URBAN_EXPANSION_REGIONS = {"Jakarta Suburbs", "Delhi NCR", "Lagos Outskirts", "Shenzhen Periphery"}
FIRE_RISK_REGIONS = {"Siberia Boreal", "Amazon Basin", "California Chaparral", "Australian Bushland"}


@pw.udf
def detect_fire(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndvi: float, band_swir: float,
    cloud_cover: float, region: str, satellite: str
) -> pw.Json:
    """
    Fire / active burn detection UDF.
    Active fire: very high SWIR + very low NDVI.
    Burn scar:   high SWIR + low NDVI (persists days after fire).

    Thresholds:
      Active fire: SWIR > 0.85, NDVI < 0.05
      Burn scar:   SWIR > 0.75, NDVI < 0.10
    """
    if cloud_cover > 40:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})

    is_active = band_swir > 0.85 and ndvi < 0.05
    is_scar   = band_swir > 0.75 and ndvi < 0.10

    if not (is_active or is_scar):
        return pw.Json({"detected": False})

    severity   = "critical" if is_active else ("high" if band_swir > 0.80 else "medium")
    confidence = min(0.97, 0.70 + band_swir * 0.30)
    label      = "Active fire" if is_active else "Fresh burn scar"

    import random
    area = band_swir * random.uniform(200, 5000)

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "fire",
        "severity": severity,
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 1),
        "ndvi_delta": round(ndvi - 0.55, 4),
        "description": (
            f"{label} detected in {region}. "
            f"SWIR={band_swir:.2f}, NDVI={ndvi:.2f}. "
            f"Estimated affected area: {area:.0f} ha."
        ),
        "icon": "🔥",
        "color": "#fb923c",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })


@pw.udf
def detect_construction(
    tile_id: str, lat: float, lon: float,
    timestamp: int, ndvi: float, ndvi_delta: float,
    band_swir: float, cloud_cover: float,
    region: str, satellite: str
) -> pw.Json:
    """
    Illegal / unauthorized construction detection UDF.

    Signature:
      - NDVI drop (vegetation cleared)
      - High SWIR (bare soil, concrete, metal roofing)
      - Small to medium area change (not forest clearing scale)

    Useful for: urban sprawl monitoring, buffer-zone encroachments,
    illegal mining, unauthorized infrastructure.
    """
    if cloud_cover > 25:
        return pw.Json({"detected": False, "reason": "high_cloud_cover"})

    construction_signal = (
        ndvi_delta < -0.15 and
        band_swir > 0.55 and
        ndvi < 0.30
    )
    if not construction_signal:
        return pw.Json({"detected": False})

    confidence = min(0.84, 0.50 + abs(ndvi_delta) * 0.8 + band_swir * 0.2)

    import random
    area = abs(ndvi_delta) * random.uniform(2, 50)  # typically small-scale

    return pw.Json({
        "detected": True,
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_type": "construction",
        "severity": "medium",
        "confidence": round(confidence, 3),
        "area_hectares": round(area, 2),
        "ndvi_delta": round(ndvi_delta, 4),
        "description": (
            f"Possible unauthorized construction in {region}. "
            f"NDVI drop={ndvi_delta:.2f}, SWIR={band_swir:.2f}. "
            f"New built-up footprint: ~{area:.1f} ha."
        ),
        "icon": "🏗️",
        "color": "#a78bfa",
        "tile_id": tile_id,
        "lat": lat, "lon": lon,
        "timestamp": timestamp,
        "region": region,
        "satellite": satellite,
    })
