"""
alerts/alert_router.py
Routes detected change events to external channels based on severity.

  critical → Slack + Email + SMS (immediate)
  high     → Slack + Email
  medium   → Slack
  low      → Logged only (no external alert)
"""
import os
import json
import time
import smtplib
import requests
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pathway as pw


# ── Config ────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
EMAIL_FROM        = os.getenv("ALERT_EMAIL_FROM", "")
EMAIL_PASSWORD    = os.getenv("ALERT_EMAIL_PASSWORD", "")
EMAIL_TO          = os.getenv("ALERT_EMAIL_TO", "")
SMTP_HOST         = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT         = int(os.getenv("SMTP_PORT", "587"))
TWILIO_SID        = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM       = os.getenv("TWILIO_FROM_NUMBER", "")
ALERT_SMS_TO      = os.getenv("ALERT_SMS_TO", "")

SEVERITY_CHANNELS = {
    "critical": ["slack", "email", "sms"],
    "high":     ["slack", "email"],
    "medium":   ["slack"],
    "low":      [],
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
}


def format_alert_message(event: dict) -> str:
    emoji = SEVERITY_EMOJI.get(event.get("severity", "low"), "⚪")
    return (
        f"{emoji} *SENTINEL//WATCH ALERT*\n"
        f"*Type:* {event['icon']} {event['event_type'].replace('_', ' ').title()}\n"
        f"*Severity:* {event['severity'].upper()}\n"
        f"*Region:* {event['region']}\n"
        f"*Confidence:* {event['confidence']*100:.0f}%\n"
        f"*Area:* {event['area_hectares']:,.0f} ha\n"
        f"*Satellite:* {event['satellite']}\n"
        f"*Coords:* {event['lat']:.3f}, {event['lon']:.3f}\n"
        f"*Details:* {event['description']}\n"
        f"*Event ID:* `{event['event_id']}`"
    )


def send_slack(event: dict) -> bool:
    if not SLACK_WEBHOOK_URL:
        print(f"[Alert] Slack not configured — would send: {event['event_id']}")
        return False
    try:
        payload = {
            "text": format_alert_message(event),
            "attachments": [{
                "color": event.get("color", "#ff0000"),
                "fields": [
                    {"title": "Tile ID", "value": event["tile_id"], "short": True},
                    {"title": "NDVI Delta", "value": f"{event['ndvi_delta']:.3f}", "short": True},
                ]
            }]
        }
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[Alert] Slack sent: {event['event_id']}")
        return True
    except Exception as e:
        print(f"[Alert] Slack failed: {e}")
        return False


def send_email(event: dict) -> bool:
    if not all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO]):
        print(f"[Alert] Email not configured — would send: {event['event_id']}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{event['severity'].upper()}] {event['event_type'].title()} detected — {event['region']}"
        msg["From"]    = EMAIL_FROM
        msg["To"]      = EMAIL_TO

        body = format_alert_message(event).replace("*", "").replace("`", "")
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"[Alert] Email sent: {event['event_id']}")
        return True
    except Exception as e:
        print(f"[Alert] Email failed: {e}")
        return False


def send_sms(event: dict) -> bool:
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, ALERT_SMS_TO]):
        print(f"[Alert] SMS not configured — would send: {event['event_id']}")
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        body = (
            f"SENTINEL ALERT [{event['severity'].upper()}] "
            f"{event['event_type'].title()} in {event['region']}. "
            f"Confidence: {event['confidence']*100:.0f}%. "
            f"Area: {event['area_hectares']:.0f}ha. "
            f"ID: {event['event_id']}"
        )
        client.messages.create(to=ALERT_SMS_TO, from_=TWILIO_FROM, body=body)
        print(f"[Alert] SMS sent: {event['event_id']}")
        return True
    except Exception as e:
        print(f"[Alert] SMS failed: {e}")
        return False


def dispatch_alert(event: dict) -> None:
    """Dispatch alert to all configured channels for this severity level."""
    severity  = event.get("severity", "low")
    channels  = SEVERITY_CHANNELS.get(severity, [])
    if not channels:
        return

    print(f"[Alert] Dispatching {event['event_id']} ({severity}) → {channels}")

    threads = []
    if "slack" in channels:
        threads.append(threading.Thread(target=send_slack, args=(event,), daemon=True))
    if "email" in channels:
        threads.append(threading.Thread(target=send_email, args=(event,), daemon=True))
    if "sms" in channels:
        threads.append(threading.Thread(target=send_sms, args=(event,), daemon=True))

    for t in threads:
        t.start()


@pw.udf
def route_alert(
    event_id: str, event_type: str, severity: str,
    confidence: float, area_hectares: float, region: str,
    lat: float, lon: float, description: str,
    tile_id: str, satellite: str, timestamp: int,
    icon: str, color: str, ndvi_delta: float,
) -> pw.Json:
    """
    Pathway UDF — called on every detected event row.
    Dispatches alerts asynchronously (non-blocking).
    """
    event = {
        "event_id": event_id, "event_type": event_type, "severity": severity,
        "confidence": confidence, "area_hectares": area_hectares, "region": region,
        "lat": lat, "lon": lon, "description": description, "tile_id": tile_id,
        "satellite": satellite, "timestamp": timestamp, "icon": icon, "color": color,
        "ndvi_delta": ndvi_delta,
    }
    dispatch_alert(event)
    return pw.Json({"alert_dispatched": True, "channels": SEVERITY_CHANNELS.get(severity, [])})
