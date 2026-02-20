"""
detection/vision_model.py
Vision model UDF — calls GPT-4V or Claude Vision on each satellite tile.

This runs AFTER spectral index pre-filtering to avoid unnecessary API calls.
Only tiles flagged as "suspicious" by ndvi/ndwi/swir detectors are sent here.

Supports:
  - OpenAI GPT-4V
  - Anthropic Claude (claude-opus-4-6)
  - Prithvi-EO-2.0 (NASA geospatial foundation model — best for satellite imagery)
"""
import pathway as pw
import json
import os
import base64
from typing import Optional


# ── Config (set via environment variables) ────────────────────────
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "anthropic")  # anthropic | openai | prithvi
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

VISION_PROMPT = """You are analyzing a Sentinel-2 false-color composite satellite image.
Bands displayed: SWIR (R), NIR (G), Red (B).

Analyze this image and detect any of the following:
1. Deforestation / vegetation clearing
2. Flood / water body expansion
3. Active fire or burn scar
4. Illegal construction or built-up area expansion
5. Crop stress / agricultural anomaly

Respond with ONLY a JSON object:
{
  "event_detected": true/false,
  "event_type": "deforestation|flood|fire|construction|crop_stress|none",
  "severity": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "area_estimate_ha": <number or null>,
  "description": "<1 sentence explanation>",
  "bounding_box": {"x1": 0-1, "y1": 0-1, "x2": 0-1, "y2": 0-1} or null
}"""


def call_anthropic_vision(image_base64: str, media_type: str = "image/png") -> dict:
    """Call Claude claude-opus-4-6 with satellite image."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_base64}
                },
                {"type": "text", "text": VISION_PROMPT}
            ]
        }]
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def call_openai_vision(image_base64: str, media_type: str = "image/png") -> dict:
    """Call GPT-4V with satellite image."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{image_base64}"}
                },
                {"type": "text", "text": VISION_PROMPT}
            ]
        }]
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


@pw.udf
def vision_model_classify(
    tile_id: str, image_base64: str,
    pre_detected_type: str, region: str,
    lat: float, lon: float, timestamp: int, satellite: str,
) -> pw.Json:
    """
    Pathway UDF: runs vision model classification on a tile image.

    Args:
        tile_id         : unique tile identifier
        image_base64    : base64-encoded PNG of the false-color composite
        pre_detected_type: event type flagged by spectral detectors (confirmation step)
        region, lat, lon, timestamp, satellite: metadata

    Returns:
        pw.Json with detection result (same schema as spectral detectors)
    """
    if not image_base64:
        return pw.Json({"detected": False, "reason": "no_image_data"})

    try:
        if VISION_PROVIDER == "anthropic":
            result = call_anthropic_vision(image_base64)
        elif VISION_PROVIDER == "openai":
            result = call_openai_vision(image_base64)
        else:
            # Prithvi-EO-2.0 — local model inference
            # from prithvi import PrithviModel
            # result = PrithviModel.infer(image_base64)
            return pw.Json({"detected": False, "reason": "prithvi_not_configured"})

        if not result.get("event_detected"):
            return pw.Json({"detected": False, "reason": "vision_model_no_event"})

        import uuid
        return pw.Json({
            "detected": True,
            "event_id": f"VIS_{uuid.uuid4().hex[:8].upper()}",
            "event_type": result.get("event_type", pre_detected_type),
            "severity": result.get("severity", "medium"),
            "confidence": result.get("confidence", 0.75),
            "area_hectares": result.get("area_estimate_ha", 0),
            "ndvi_delta": 0.0,
            "description": result.get("description", ""),
            "bounding_box": result.get("bounding_box"),
            "source": "vision_model",
            "provider": VISION_PROVIDER,
            "tile_id": tile_id,
            "lat": lat, "lon": lon,
            "timestamp": timestamp,
            "region": region,
            "satellite": satellite,
        })

    except json.JSONDecodeError as e:
        return pw.Json({"detected": False, "reason": f"json_parse_error: {e}"})
    except Exception as e:
        return pw.Json({"detected": False, "reason": f"api_error: {str(e)}"})
