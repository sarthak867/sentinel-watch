"""
schemas.py — Pathway table schemas for all data models
"""
import pathway as pw


class SatelliteTileSchema(pw.Schema):
    """Raw tile arriving from Sentinel-2 / Landsat-8"""
    tile_id: str
    satellite: str          # "Sentinel-2" | "Landsat-8"
    lat: float
    lon: float
    timestamp: int          # unix ms
    ndvi: float             # Normalized Difference Vegetation Index (-1 to 1)
    ndwi: float             # Normalized Difference Water Index (-1 to 1)
    band_swir: float        # Short-wave infrared reflectance (0-1)
    cloud_cover: float      # 0-100 %
    resolution_m: int       # meters per pixel (10, 20, 30)
    region: str             # human-readable region name


class ChangeEventSchema(pw.Schema):
    """Detected change event produced by the pipeline"""
    event_id: str
    tile_id: str
    event_type: str         # deforestation | flood | construction | crop_stress | fire
    severity: str           # low | medium | high | critical
    confidence: float       # 0-1
    lat: float
    lon: float
    area_hectares: float
    ndvi_delta: float
    timestamp: int
    region: str
    satellite: str
    description: str
    icon: str
    color: str


class RegionBaselineSchema(pw.Schema):
    """Historical baseline values per region"""
    region: str
    baseline_ndvi: float
    baseline_ndwi: float
    baseline_swir: float
    last_updated: int


class AlertSchema(pw.Schema):
    """Alert record sent to external channels"""
    alert_id: str
    event_id: str
    channel: str            # slack | email | sms | webhook
    severity: str
    message: str
    sent_at: int
    status: str             # pending | sent | failed
