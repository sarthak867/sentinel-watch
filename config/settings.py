"""
config/settings.py
Central configuration — all values from environment variables.
Copy .env.example to .env and fill in your keys.
"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    # ── Satellite API Keys ──────────────────────────────────────
    usgs_username: str  = os.getenv("USGS_USERNAME", "")
    usgs_password: str  = os.getenv("USGS_PASSWORD", "")
    # Copernicus: no key needed for public data

    # ── Vision Model ────────────────────────────────────────────
    vision_provider: str    = os.getenv("VISION_PROVIDER", "anthropic")  # anthropic|openai|prithvi
    anthropic_api_key: str  = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str     = os.getenv("OPENAI_API_KEY", "")

    # ── Kafka ───────────────────────────────────────────────────
    kafka_brokers: str      = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_sentinel_topic: str = os.getenv("KAFKA_SENTINEL_TOPIC", "sentinel2-tiles")
    kafka_landsat_topic: str  = os.getenv("KAFKA_LANDSAT_TOPIC",  "landsat8-tiles")
    kafka_events_topic: str   = os.getenv("KAFKA_EVENTS_TOPIC",   "change-events")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "sentinel-watch")

    # ── Alert Channels ──────────────────────────────────────────
    slack_webhook_url: str  = os.getenv("SLACK_WEBHOOK_URL",   "")
    alert_email_from: str   = os.getenv("ALERT_EMAIL_FROM",    "")
    alert_email_password: str = os.getenv("ALERT_EMAIL_PASSWORD", "")
    alert_email_to: str     = os.getenv("ALERT_EMAIL_TO",      "")
    smtp_host: str          = os.getenv("SMTP_HOST",           "smtp.gmail.com")
    smtp_port: int          = int(os.getenv("SMTP_PORT",       "587"))
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID",  "")
    twilio_auth_token: str  = os.getenv("TWILIO_AUTH_TOKEN",   "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER",  "")
    alert_sms_to: str       = os.getenv("ALERT_SMS_TO",        "")

    # ── Servers ─────────────────────────────────────────────────
    api_host: str           = os.getenv("API_HOST",            "0.0.0.0")
    api_port: int           = int(os.getenv("API_PORT",        "8765"))
    ws_host: str            = os.getenv("WS_HOST",             "0.0.0.0")
    ws_port: int            = int(os.getenv("WS_PORT",         "8766"))

    # ── Detection Thresholds ─────────────────────────────────────
    deforestation_ndvi_threshold: float  = float(os.getenv("DEFORESTATION_THRESHOLD", "-0.25"))
    flood_ndwi_threshold: float          = float(os.getenv("FLOOD_THRESHOLD",          "0.25"))
    fire_swir_threshold: float           = float(os.getenv("FIRE_SWIR_THRESHOLD",      "0.75"))
    max_cloud_cover: float               = float(os.getenv("MAX_CLOUD_COVER",          "30"))

    # ── Data Polling ─────────────────────────────────────────────
    sentinel_poll_interval_s: int  = int(os.getenv("SENTINEL_POLL_INTERVAL", "300"))  # 5 min
    landsat_poll_interval_s: int   = int(os.getenv("LANDSAT_POLL_INTERVAL",  "600"))  # 10 min


settings = Settings()
