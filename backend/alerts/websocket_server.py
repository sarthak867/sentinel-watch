"""
alerts/websocket_server.py
WebSocket server — broadcasts live change events to the React dashboard.

Frontend connects to ws://localhost:8766 and receives JSON events
the moment Pathway detects them.
"""
import asyncio
import json
import threading
import time
from collections import deque
from typing import Set
import websockets
import websockets.server


# Shared queue between Pathway pipeline thread and WebSocket server
_event_queue: deque = deque(maxlen=1000)
_connected_clients: Set = set()
_lock = threading.Lock()


def push_event(event: dict) -> None:
    """Called from Pathway pipeline to enqueue a new event."""
    with _lock:
        _event_queue.append(event)


async def _handle_client(websocket) -> None:
    """Handle a single WebSocket client connection."""
    _connected_clients.add(websocket)
    client_addr = websocket.remote_address
    print(f"[WS] Client connected: {client_addr} | Total: {len(_connected_clients)}")

    try:
        # Send recent event history on connect
        with _lock:
            history = list(_event_queue)[-20:]
        if history:
            await websocket.send(json.dumps({"type": "history", "events": history}))

        # Keep connection alive
        async for message in websocket:
            if message == "ping":
                await websocket.send("pong")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _connected_clients.discard(websocket)
        print(f"[WS] Client disconnected: {client_addr} | Total: {len(_connected_clients)}")


async def _broadcast_loop() -> None:
    """Continuously broadcast new events from the queue to all clients."""
    global _connected_clients
    last_size = 0
    while True:
        with _lock:
            current_size = len(_event_queue)
            if current_size > last_size:
                new_events = list(_event_queue)[last_size:]
                last_size = current_size
            else:
                new_events = []

        if new_events and _connected_clients:
            payload = json.dumps({"type": "new_events", "events": new_events})
            dead = set()
            for client in list(_connected_clients):
                try:
                    await client.send(payload)
                except websockets.exceptions.ConnectionClosed:
                    dead.add(client)
            _connected_clients -= dead

        await asyncio.sleep(0.5)


async def _run_server(host: str = "0.0.0.0", port: int = 8766) -> None:
    print(f"[WS] WebSocket server starting on ws://{host}:{port}")
    async with websockets.serve(_handle_client, host, port):
        await _broadcast_loop()


def start_websocket_server(host: str = "0.0.0.0", port: int = 8766) -> threading.Thread:
    """Start WebSocket server in a background thread."""
    def _run():
        asyncio.run(_run_server(host, port))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    print(f"[WS] Server thread started on port {port}")
    return thread
