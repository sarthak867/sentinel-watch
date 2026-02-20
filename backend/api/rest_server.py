"""
api/rest_server.py
REST API server — serves data to the React dashboard.

Endpoints:
  GET /api/events        → recent change events (last 100)
  GET /api/tiles         → recent tile metadata
  GET /api/stats         → pipeline stats
  GET /api/world-model   → current knowledge graph state per region
  GET /api/health        → health check
"""
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs


# Shared state — populated by the Pathway pipeline
_state = {
    "events":      [],   # list of ChangeEvent dicts (last 200)
    "tiles":       [],   # list of SatelliteTile dicts (last 500)
    "world_model": {},   # region → current state dict
    "stats": {
        "tiles_processed":  0,
        "events_detected":  0,
        "tiles_per_second": 0.0,
        "pipeline_latency_ms": 0,
        "uptime_seconds":   0,
        "start_time":       int(time.time()),
    },
}
_lock = threading.Lock()


def update_events(new_events: list) -> None:
    with _lock:
        _state["events"] = (new_events + _state["events"])[:200]
        _state["stats"]["events_detected"] = len(_state["events"])


def update_tiles(new_tiles: list) -> None:
    with _lock:
        _state["tiles"] = (new_tiles + _state["tiles"])[:500]
        _state["stats"]["tiles_processed"] += len(new_tiles)


def update_world_model(region: str, data: dict) -> None:
    with _lock:
        _state["world_model"][region] = data


def update_stats(rate: float, latency_ms: int) -> None:
    with _lock:
        _state["stats"]["tiles_per_second"] = rate
        _state["stats"]["pipeline_latency_ms"] = latency_ms
        _state["stats"]["uptime_seconds"] = int(time.time()) - _state["stats"]["start_time"]


class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress noisy access logs

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)
        path   = parsed.path

        with _lock:
            if path == "/api/events":
                limit = int(qs.get("limit", [100])[0])
                event_type = qs.get("type", [None])[0]
                events = _state["events"]
                if event_type:
                    events = [e for e in events if e.get("event_type") == event_type]
                self._send_json(events[:limit])

            elif path == "/api/tiles":
                limit = int(qs.get("limit", [50])[0])
                self._send_json(_state["tiles"][:limit])

            elif path == "/api/stats":
                self._send_json(_state["stats"])

            elif path == "/api/world-model":
                self._send_json(_state["world_model"])

            elif path == "/api/health":
                self._send_json({
                    "status": "ok",
                    "uptime": int(time.time()) - _state["stats"]["start_time"],
                    "events": _state["stats"]["events_detected"],
                    "tiles":  _state["stats"]["tiles_processed"],
                })
            else:
                self._send_json({"error": "not found"}, 404)


def start_rest_server(host: str = "0.0.0.0", port: int = 8765) -> threading.Thread:
    """Start REST API server in background thread."""
    server = HTTPServer((host, port), APIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[API] REST server started on http://{host}:{port}")
    return thread
