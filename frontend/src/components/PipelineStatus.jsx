// components/PipelineStatus.jsx
import { PIPELINE_STAGES } from "../utils/eventConfig";

const STATUS_COLOR = { active: "#22c55e", standby: "#f59e0b", error: "#ef4444" };

export default function PipelineStatus({ stats }) {
  return (
    <div>
      {PIPELINE_STAGES.map((stage) => (
        <div key={stage.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
          <div style={{
            width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
            background: STATUS_COLOR[stage.status] || "#888",
            boxShadow: stage.status === "active" ? `0 0 6px ${STATUS_COLOR.active}` : "none",
          }} />
          <div style={{ flex: 1, fontSize: 11, color: "rgba(255,255,255,0.55)" }}>{stage.label}</div>
          <div style={{ fontSize: 9, color: STATUS_COLOR[stage.status] || "#888", letterSpacing: 1 }}>
            {stage.status.toUpperCase()}
          </div>
        </div>
      ))}

      {/* Throughput bar */}
      {stats && (
        <div style={{ marginTop: 12, padding: "8px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.3)", letterSpacing: 1.5 }}>THROUGHPUT</span>
            <span style={{ fontSize: 11, fontWeight: 600, color: "#38bdf8" }}>
              {stats.tiles_per_second} tiles/sec
            </span>
          </div>
          <div style={{ height: 2, background: "rgba(255,255,255,0.06)", borderRadius: 1 }}>
            <div style={{
              width: `${Math.min(100, (stats.tiles_per_second / 20) * 100)}%`,
              height: "100%", background: "#38bdf8", borderRadius: 1,
              transition: "width 0.8s ease",
            }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)" }}>
              Latency: {stats.pipeline_latency_ms}ms
            </span>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)" }}>
              Uptime: {Math.floor(stats.uptime_seconds / 60)}m
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
