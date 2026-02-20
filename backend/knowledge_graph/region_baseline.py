"""
knowledge_graph/region_baseline.py
Historical spectral index baselines for each monitored region.

In production: baselines computed from 12-month rolling average
using Pathway's temporal windowing:
  pw.temporal.sliding(hop=timedelta(days=1), duration=timedelta(days=365))

For the hackathon: hardcoded values derived from published datasets.
Sources: MODIS Land Cover, ESA CCI Land Cover, Hansen Global Forest Watch
"""

# Format: region → {ndvi, ndwi, swir, seasonal_std_ndvi}
REGION_BASELINES = {
    "Amazon Basin": {
        "ndvi": 0.72,
        "ndwi": 0.05,
        "swir": 0.15,
        "seasonal_std_ndvi": 0.06,
        "land_cover": "tropical_forest",
        "country": "Brazil / Peru / Colombia",
    },
    "Bangladesh Delta": {
        "ndvi": 0.45,
        "ndwi": 0.20,
        "swir": 0.22,
        "seasonal_std_ndvi": 0.12,
        "land_cover": "cropland_wetland",
        "country": "Bangladesh",
    },
    "Punjab Farmlands": {
        "ndvi": 0.58,
        "ndwi": -0.10,
        "swir": 0.28,
        "seasonal_std_ndvi": 0.18,  # high — two crop seasons
        "land_cover": "irrigated_cropland",
        "country": "India / Pakistan",
    },
    "Jakarta Suburbs": {
        "ndvi": 0.41,
        "ndwi": -0.05,
        "swir": 0.38,
        "seasonal_std_ndvi": 0.07,
        "land_cover": "urban_fringe",
        "country": "Indonesia",
    },
    "Siberia Boreal": {
        "ndvi": 0.55,
        "ndwi": -0.02,
        "swir": 0.18,
        "seasonal_std_ndvi": 0.22,  # extreme seasonality
        "land_cover": "boreal_forest",
        "country": "Russia",
    },
    "Sahel Region": {
        "ndvi": 0.38,
        "ndwi": -0.15,
        "swir": 0.35,
        "seasonal_std_ndvi": 0.15,
        "land_cover": "dryland_mosaic",
        "country": "Mali / Niger / Chad",
    },
    "Congo Basin": {
        "ndvi": 0.75,
        "ndwi": 0.08,
        "swir": 0.12,
        "seasonal_std_ndvi": 0.05,
        "land_cover": "tropical_forest",
        "country": "DRC / Congo",
    },
    "California Chaparral": {
        "ndvi": 0.42,
        "ndwi": -0.18,
        "swir": 0.32,
        "seasonal_std_ndvi": 0.14,
        "land_cover": "shrubland",
        "country": "United States",
    },
}


def get_baseline(region: str) -> dict:
    """Get baseline for a region, with fallback defaults."""
    return REGION_BASELINES.get(region, {
        "ndvi": 0.50,
        "ndwi": 0.00,
        "swir": 0.25,
        "seasonal_std_ndvi": 0.10,
        "land_cover": "unknown",
        "country": "unknown",
    })


def compute_ndvi_delta(ndvi: float, region: str) -> float:
    baseline = get_baseline(region)["ndvi"]
    return round(ndvi - baseline, 4)


def compute_ndwi_delta(ndwi: float, region: str) -> float:
    baseline = get_baseline(region)["ndwi"]
    return round(ndwi - baseline, 4)


def is_anomaly(ndvi_delta: float, region: str, sigma_threshold: float = 2.0) -> bool:
    """True if NDVI delta exceeds N standard deviations from norm."""
    std = get_baseline(region).get("seasonal_std_ndvi", 0.10)
    return abs(ndvi_delta) > (sigma_threshold * std)
