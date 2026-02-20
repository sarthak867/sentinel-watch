// hooks/useStats.js
// Polls the REST API for live pipeline statistics

import { useState, useEffect, useRef } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8765";
const POLL_INTERVAL = 3000; // ms

/**
 * useStats
 * Periodically polls /api/stats and /api/world-model.
 *
 * Returns:
 *   stats       - { tiles_processed, events_detected, tiles_per_second, pipeline_latency_ms }
 *   worldModel  - { region: { current_ndvi, active_events, ... } }
 *   loading     - initial loading state
 */
export function useStats() {
  const [stats, setStats] = useState({
    tiles_processed:    0,
    events_detected:    0,
    tiles_per_second:   0,
    pipeline_latency_ms: 0,
    uptime_seconds:     0,
  });
  const [worldModel, setWorldModel] = useState({});
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);

  const fetchStats = async () => {
    try {
      const [statsRes, modelRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats`),
        fetch(`${API_BASE}/api/world-model`),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (modelRes.ok) setWorldModel(await modelRes.json());
    } catch {
      // Backend not running — silently ignore (demo mode)
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    timerRef.current = setInterval(fetchStats, POLL_INTERVAL);
    return () => clearInterval(timerRef.current);
  }, []);

  return { stats, worldModel, loading };
}
