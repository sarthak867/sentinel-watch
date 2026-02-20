"""
connectors/kafka_connector.py
Production Kafka connector for real-time satellite tile ingestion.

Architecture:
  Satellite downlink → Ground station → Preprocessing service
  → Kafka topic (sentinel2-tiles / landsat-tiles) → Pathway pipeline

Why Kafka?
  - Decouples satellite feed from processing pipeline
  - Handles burst traffic (100s of tiles during satellite pass)
  - Enables replay for debugging / backfill
  - Multiple consumers: Pathway + archival + alerting
"""
import pathway as pw
import os
from ..schemas import SatelliteTileSchema


KAFKA_BROKERS    = os.getenv("KAFKA_BROKERS", "localhost:9092")
SENTINEL_TOPIC   = os.getenv("KAFKA_SENTINEL_TOPIC", "sentinel2-tiles")
LANDSAT_TOPIC    = os.getenv("KAFKA_LANDSAT_TOPIC", "landsat8-tiles")
CONSUMER_GROUP   = os.getenv("KAFKA_CONSUMER_GROUP", "sentinel-watch-pipeline")


def create_kafka_sentinel_table() -> pw.Table:
    """
    Read Sentinel-2 tiles from Kafka topic using Pathway's native Kafka connector.

    Message format (JSON):
    {
      "tile_id": "S2_...",
      "satellite": "Sentinel-2",
      "lat": 23.45,
      "lon": 90.12,
      "timestamp": 1700000000000,
      "ndvi": 0.68,
      "ndwi": -0.12,
      "band_swir": 0.24,
      "cloud_cover": 8.5,
      "resolution_m": 10,
      "region": "Bangladesh Delta"
    }
    """
    rdkafka_settings = {
        "bootstrap.servers": KAFKA_BROKERS,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "latest",
        "enable.auto.commit": "true",
        "security.protocol": "PLAINTEXT",
    }

    return pw.io.kafka.read(
        rdkafka_settings=rdkafka_settings,
        topic=SENTINEL_TOPIC,
        schema=SatelliteTileSchema,
        format="json",
        autocommit_duration_ms=1000,
    )


def create_kafka_landsat_table() -> pw.Table:
    """Read Landsat-8 tiles from Kafka."""
    rdkafka_settings = {
        "bootstrap.servers": KAFKA_BROKERS,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "latest",
        "enable.auto.commit": "true",
    }

    return pw.io.kafka.read(
        rdkafka_settings=rdkafka_settings,
        topic=LANDSAT_TOPIC,
        schema=SatelliteTileSchema,
        format="json",
        autocommit_duration_ms=1000,
    )


def create_merged_satellite_table() -> pw.Table:
    """
    Merge Sentinel-2 and Landsat-8 streams into a single table.
    Pathway handles concurrent reads natively via differential dataflow.
    """
    sentinel = create_kafka_sentinel_table()
    landsat  = create_kafka_landsat_table()
    return sentinel.concat(landsat)


def write_events_to_kafka(events_table: pw.Table, topic: str = "change-events") -> None:
    """
    Write detected change events back to Kafka for downstream consumers.
    (Alerting service, archival, dashboard WebSocket bridge, etc.)
    """
    pw.io.kafka.write(
        events_table,
        rdkafka_settings={
            "bootstrap.servers": KAFKA_BROKERS,
            "security.protocol": "PLAINTEXT",
        },
        topic_name=topic,
        format="json",
    )
