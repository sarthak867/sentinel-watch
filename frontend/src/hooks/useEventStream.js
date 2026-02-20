// hooks/useEventStream.js
// WebSocket hook — receives live change events from Pathway backend

import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8766";

/**
 * useEventStream
 * Connects to the Pathway WebSocket broadcast and maintains a live
 * event list in React state.
 *
 * Returns:
 *   events      - array of all received events (newest first)
 *   feed        - most recent 20 events for the live feed panel
 *   connected   - WebSocket connection status
 *   latestEvent - the single most recently received event
 */
export function useEventStream(maxEvents = 200) {
  const [events,      setEvents]      = useState([]);
  const [feed,        setFeed]        = useState([]);
  const [connected,   setConnected]   = useState(false);
  const [latestEvent, setLatestEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        console.log("[WS] Connected to Pathway stream");
        clearTimeout(reconnectTimer.current);
      };

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);

          if (msg.type === "history") {
            // Initial history dump on connect
            setEvents(msg.events.slice(0, maxEvents));
            setFeed(msg.events.slice(0, 20));
          } else if (msg.type === "new_events") {
            const newEvts = msg.events;
            setLatestEvent(newEvts[0] || null);
            setEvents((prev) => [...newEvts, ...prev].slice(0, maxEvents));
            setFeed((prev) => [...newEvts, ...prev].slice(0, 20));
          }
        } catch (err) {
          console.error("[WS] Parse error:", err);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        console.log("[WS] Disconnected — reconnecting in 3s...");
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        ws.close();
      };
    } catch (err) {
      console.error("[WS] Could not connect:", err);
      reconnectTimer.current = setTimeout(connect, 3000);
    }
  }, [maxEvents]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { events, feed, connected, latestEvent };
}
