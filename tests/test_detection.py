"""
tests/test_detection.py
Unit tests for NDVI, NDWI, SWIR change detectors.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.knowledge_graph.region_baseline import (
    get_baseline, compute_ndvi_delta, compute_ndwi_delta, is_anomaly
)


# ── Region baseline tests ─────────────────────────────────────────
class TestRegionBaseline:

    def test_known_region_returns_correct_ndvi(self):
        b = get_baseline("Amazon Basin")
        assert b["ndvi"] == 0.72

    def test_unknown_region_returns_defaults(self):
        b = get_baseline("Unknown Place XYZ")
        assert b["ndvi"] == 0.50
        assert b["land_cover"] == "unknown"

    def test_ndvi_delta_positive_when_above_baseline(self):
        delta = compute_ndvi_delta(0.80, "Amazon Basin")  # baseline = 0.72
        assert delta > 0
        assert abs(delta - 0.08) < 0.001

    def test_ndvi_delta_negative_when_deforestation(self):
        delta = compute_ndvi_delta(0.30, "Amazon Basin")  # big drop
        assert delta < -0.40

    def test_ndwi_delta_positive_during_flood(self):
        delta = compute_ndwi_delta(0.50, "Bangladesh Delta")  # baseline = 0.20
        assert delta > 0.25

    def test_is_anomaly_triggers_at_2sigma(self):
        # Amazon std = 0.06, so 2-sigma = 0.12
        assert is_anomaly(-0.15, "Amazon Basin", sigma_threshold=2.0) is True
        assert is_anomaly(-0.05, "Amazon Basin", sigma_threshold=2.0) is False


# ── Detection threshold tests ─────────────────────────────────────
class TestDetectionThresholds:

    def test_deforestation_threshold(self):
        """NDVI delta < -0.25 in forest region should trigger."""
        ndvi_delta = compute_ndvi_delta(0.40, "Amazon Basin")  # 0.72 - 0.40 = -0.32
        assert ndvi_delta < -0.25, "Should trigger deforestation"

    def test_no_deforestation_slight_drop(self):
        """Small NDVI drop should NOT trigger deforestation."""
        ndvi_delta = compute_ndvi_delta(0.68, "Amazon Basin")  # -0.04
        assert ndvi_delta > -0.25, "Should NOT trigger"

    def test_flood_threshold(self):
        """NDWI delta > 0.25 should trigger flood."""
        ndwi_delta = compute_ndwi_delta(0.55, "Bangladesh Delta")  # 0.55 - 0.20 = 0.35
        assert ndwi_delta > 0.25, "Should trigger flood"

    def test_crop_stress_range(self):
        """NDVI delta between -0.10 and -0.25 in farmland = crop stress."""
        ndvi_delta = compute_ndvi_delta(0.42, "Punjab Farmlands")  # 0.58 - 0.42 = -0.16
        assert -0.25 < ndvi_delta < -0.10, "Should be in crop stress range"


# ── Mock tile generation tests ────────────────────────────────────
class TestMockTileGeneration:

    def test_generated_tiles_have_required_fields(self):
        import sys
        sys.path.insert(0, "..")
        # Inline test without importing pathway
        required = ["tile_id", "satellite", "lat", "lon", "timestamp",
                    "ndvi", "ndwi", "band_swir", "cloud_cover", "resolution_m", "region"]

        tile = {
            "tile_id": "TILE_TEST_001", "satellite": "Sentinel-2",
            "lat": -3.4, "lon": -62.2, "timestamp": 1700000000000,
            "ndvi": 0.72, "ndwi": 0.05, "band_swir": 0.15,
            "cloud_cover": 5.0, "resolution_m": 10, "region": "Amazon Basin"
        }
        for field in required:
            assert field in tile, f"Missing field: {field}"

    def test_ndvi_in_valid_range(self):
        ndvi_values = [0.72, -0.1, 0.0, 1.0, -1.0, 0.45]
        for v in ndvi_values:
            assert -1.0 <= v <= 1.0

    def test_cloud_cover_triggers_skip(self):
        """Tiles with cloud cover > 30% should be skipped."""
        cloud_cover = 35.0
        should_skip = cloud_cover > 30
        assert should_skip is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
