// App.jsx — Root component
// Wires all components + hooks together
import { useState, useCallback } from "react";
import WorldMap       from "./components/WorldMap";
import EventFeed      from "./components/EventFeed";
import EventGrid      from "./components/EventGrid";
import EventDetail    from "./components/EventDetail";
import PipelineStatus from "./components/PipelineStatus";
import BreakdownBars  from "./components/BreakdownBars";
import { useEventStream } from "./hooks/useEventStream";
import { useStats }       from "./hooks/useStats";
import { EVENT_CONFIG }   from "./utils/eventConfig";

// ── Fallback: generate mock data when backend is offline ──────────
import { generateMockEvents } from "./utils/mockData";

export default function App() {
  const { events: wsEvents, feed, connected, latestEvent } = useEventStream();
  const { stats, worldModel } = useStats();

  // Use mock data if no WS events yet
  const [mockEvents] = useState(() => generateMockEvents(30));
  const events = wsEvents.length > 0 ? wsEvents : mockEvents;

  const [selected, setSelected]   = useState(null);
  const [filter,   setFilter]     = useState("all");
  const [tab,      setTab]        = useState("map");

  const filteredEvents = filter === "all"
    ? events
    : events.filter((e) => e.event_type === filter);

  const criticalCount = events.filter((e) => e.severity === "critical").length;

  const handleSelect = useCallback((evt) => {
    setSelected(evt);
    setTab("map");
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#020610", color: "#e2e8f0", fontFamily: "'IBM Plex Mono', monospace", fontSize: 13, display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@300;400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #050a14; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }
        @keyframes slideIn { from { transform: translateX(-16px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
      `}</style>

      {/* ── Header ─────────────────────────────────────────────── */}
      <header style={{ background: "rgba(5,14,30,0.97)", borderBottom: "1px solid rgba(56,189,248,0.15)", padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg,#0ea5e9,#6366f1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🛰️</div>
            <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 600, fontSize: 15, letterSpacing: 1, color: "#fff" }}>SENTINEL//WATCH</span>
          </div>
          <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.12)" }} />
          <span style={{ color: "rgba(255,255,255,0.35)", fontSize: 11, letterSpacing: 2 }}>PATHWAY STREAM ENGINE v2.1</span>
        </div>

        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: connected ? "#22c55e" : "#f59e0b", animation: "blink 1.2s ease infinite" }} />
            <span style={{ fontSize: 10, letterSpacing: 2, color: connected ? "#22c55e" : "#f59e0b" }}>
              {connected ? "LIVE" : "DEMO"}
            </span>
          </div>
          {[
            { label: "TILES/SEC",  val: stats.tiles_per_second || "–" },
            { label: "LATENCY",    val: stats.pipeline_latency_ms ? `${stats.pipeline_latency_ms}ms` : "–" },
            { label: "PROCESSED",  val: (stats.tiles_processed || 0).toLocaleString() },
          ].map((s) => (
            <div key={s.label} style={{ textAlign: "center" }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#38bdf8" }}>{s.val}</div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,0.3)", letterSpacing: 1.5 }}>{s.label}</div>
            </div>
          ))}
          {criticalCount > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 6, padding: "4px 10px" }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#ef4444", animation: "blink 1.2s ease infinite" }} />
              <span style={{ fontSize: 10, color: "#ef4444", letterSpacing: 1 }}>{criticalCount} CRITICAL</span>
            </div>
          )}
        </div>
      </header>

      {/* ── Body ─────────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", flex: 1, minHeight: 0 }}>

        {/* Left panel */}
        <div style={{ padding: "16px 16px 16px 20px", display: "flex", flexDirection: "column", gap: 14, overflow: "hidden" }}>

          {/* Filter pills */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {[{ key: "all", label: "ALL", icon: "◉" }, ...Object.entries(EVENT_CONFIG).map(([k, v]) => ({ key: k, label: v.label.toUpperCase(), icon: v.icon }))].map((f) => {
              const cnt    = f.key === "all" ? events.length : events.filter((e) => e.event_type === f.key).length;
              const active = filter === f.key;
              return (
                <button key={f.key} onClick={() => setFilter(f.key)} style={{ padding: "5px 12px", borderRadius: 5, border: `1px solid ${active ? "rgba(56,189,248,0.6)" : "rgba(255,255,255,0.08)"}`, background: active ? "rgba(56,189,248,0.12)" : "transparent", color: active ? "#38bdf8" : "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: 10, letterSpacing: 1.5, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, transition: "all 0.2s" }}>
                  {f.icon} {f.label}
                  <span style={{ background: "rgba(255,255,255,0.08)", borderRadius: 3, padding: "0 4px", fontSize: 9 }}>{cnt}</span>
                </button>
              );
            })}
          </div>

          {/* Tab bar */}
          <div style={{ display: "flex", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            {[["map", "🗺 WORLD MAP"], ["grid", "⚡ EVENT GRID"]].map(([k, l]) => (
              <button key={k} onClick={() => setTab(k)} style={{ padding: "8px 16px", background: "none", border: "none", borderBottom: `2px solid ${tab === k ? "#38bdf8" : "transparent"}`, color: tab === k ? "#38bdf8" : "rgba(255,255,255,0.35)", cursor: "pointer", fontSize: 10, letterSpacing: 2, fontFamily: "inherit", marginBottom: -1 }}>
                {l}
              </button>
            ))}
          </div>

          {/* Map view */}
          {tab === "map" && (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, overflow: "hidden" }}>
              <WorldMap events={filteredEvents} selectedEvent={selected} onSelect={handleSelect} />
              <EventDetail event={selected} onClose={() => setSelected(null)} />
            </div>
          )}

          {/* Grid view */}
          {tab === "grid" && (
            <EventGrid events={filteredEvents} selectedEvent={selected} onSelect={handleSelect} />
          )}
        </div>

        {/* Right panel */}
        <div style={{ borderLeft: "1px solid rgba(255,255,255,0.06)", background: "rgba(5,14,30,0.4)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 10, letterSpacing: 2, color: "rgba(255,255,255,0.3)", marginBottom: 10 }}>PATHWAY PIPELINE</div>
            <PipelineStatus stats={stats} />
          </div>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 10, letterSpacing: 2, color: "rgba(255,255,255,0.3)", marginBottom: 10 }}>EVENT BREAKDOWN</div>
            <BreakdownBars events={events} />
          </div>
          <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "14px 16px 8px", display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ fontSize: 10, letterSpacing: 2, color: "rgba(255,255,255,0.3)" }}>STREAM FEED</div>
              <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#22c55e", animation: "blink 1.2s ease infinite" }} />
            </div>
            <EventFeed feed={feed.length > 0 ? feed : events.slice(0, 20)} onSelect={handleSelect} />
          </div>
        </div>
      </div>
    </div>
  );
}
