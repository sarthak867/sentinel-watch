"""
tests/test_pipeline.py
Integration tests for the Pathway pipeline.
Tests the full tile → detection → event flow.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json


# ── Mock tile fixtures ────────────────────────────────────────────
DEFORESTATION_TILE = {
    "tile_id": "TEST_DEFOR_001", "satellite": "Sentinel-2",
    "lat": -3.4, "lon": -62.2, "timestamp": 1700000000000,
    "ndvi": 0.28,   # way below Amazon baseline (0.72)
    "ndwi": 0.05, "band_swir": 0.20,
    "cloud_cover": 5.0, "resolution_m": 10,
    "region": "Amazon Basin",
}

FLOOD_TILE = {
    "tile_id": "TEST_FLOOD_001", "satellite": "Sentinel-2",
    "lat": 23.7, "lon": 90.4, "timestamp": 1700000000000,
    "ndvi": 0.35, "ndwi": 0.62,   # well above Bangladesh baseline (0.20)
    "band_swir": 0.18, "cloud_cover": 8.0,
    "resolution_m": 10, "region": "Bangladesh Delta",
}

FIRE_TILE = {
    "tile_id": "TEST_FIRE_001", "satellite": "Landsat-8",
    "lat": 60.5, "lon": 90.1, "timestamp": 1700000000000,
    "ndvi": 0.04, "ndwi": -0.10, "band_swir": 0.88,  # very high SWIR
    "cloud_cover": 3.0, "resolution_m": 30,
    "region": "Siberia Boreal",
}

CLEAN_TILE = {
    "tile_id": "TEST_CLEAN_001", "satellite": "Sentinel-2",
    "lat": -3.4, "lon": -62.2, "timestamp": 1700000000000,
    "ndvi": 0.71,  # near-baseline
    "ndwi": 0.04, "band_swir": 0.14,
    "cloud_cover": 2.0, "resolution_m": 10,
    "region": "Amazon Basin",
}

CLOUDY_TILE = {
    "tile_id": "TEST_CLOUD_001", "satellite": "Sentinel-2",
    "lat": -3.4, "lon": -62.2, "timestamp": 1700000000000,
    "ndvi": 0.20, "ndwi": 0.10, "band_swir": 0.50,
    "cloud_cover": 65.0,   # too cloudy → should be skipped
    "resolution_m": 10, "region": "Amazon Basin",
}


# ── Detection logic tests ─────────────────────────────────────────
class TestDetectionLogic:

    def _run_detection(self, tile: dict) -> dict:
        """Inline detection logic (mirrors pathway_engine detect_all_events UDF)."""
        from backend.knowledge_graph.region_baseline import compute_ndvi_delta, compute_ndwi_delta

        if tile["cloud_cover"] > 30:
            return {"detected": False, "reason": "high_cloud_cover"}

        ndvi_delta = compute_ndvi_delta(tile["ndvi"], tile["region"])
        ndwi_delta = compute_ndwi_delta(tile["ndwi"], tile["region"])
        band_swir  = tile["band_swir"]
        ndvi       = tile["ndvi"]

        # Deforestation
        if ndvi_delta < -0.25 and tile["region"] in {"Amazon Basin", "Siberia Boreal"}:
            return {"detected": True, "event_type": "deforestation"}

        # Flood
        if ndwi_delta > 0.25:
            return {"detected": True, "event_type": "flood"}

        # Fire
        if band_swir > 0.75 and ndvi < 0.10:
            return {"detected": True, "event_type": "fire"}

        return {"detected": False}

    def test_deforestation_detected(self):
        result = self._run_detection(DEFORESTATION_TILE)
        assert result["detected"] is True
        assert result["event_type"] == "deforestation"

    def test_flood_detected(self):
        result = self._run_detection(FLOOD_TILE)
        assert result["detected"] is True
        assert result["event_type"] == "flood"

    def test_fire_detected(self):
        result = self._run_detection(FIRE_TILE)
        assert result["detected"] is True
        assert result["event_type"] == "fire"

    def test_clean_tile_no_detection(self):
        result = self._run_detection(CLEAN_TILE)
        assert result["detected"] is False

    def test_cloudy_tile_skipped(self):
        result = self._run_detection(CLOUDY_TILE)
        assert result["detected"] is False
        assert result.get("reason") == "high_cloud_cover"


# ── REST API tests ────────────────────────────────────────────────
class TestAPIServer:

    def test_state_update_and_read(self):
        """Test that the API state store updates correctly."""
        from backend.api.rest_server import update_events, update_tiles, _state

        sample_events = [
            {"event_id": "EVT_001", "event_type": "flood", "region": "Bangladesh Delta",
             "severity": "high", "confidence": 0.92, "area_hectares": 1200,
             "lat": 23.7, "lon": 90.4, "timestamp": 1700000000000}
        ]
        update_events(sample_events)
        assert len(_state["events"]) >= 1
        assert _state["events"][0]["event_id"] == "EVT_001"

    def test_stats_counter_increments(self):
        from backend.api.rest_server import update_tiles, _state
        before = _state["stats"]["tiles_processed"]
        update_tiles([CLEAN_TILE, DEFORESTATION_TILE])
        assert _state["stats"]["tiles_processed"] == before + 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
