// components/EventDetail.jsx
import { EVENT_CONFIG, SEVERITY_CONFIG } from "../utils/eventConfig";
import { formatArea, timeAgo } from "../utils/geoUtils";

export default function EventDetail({ event, onClose }) {
  if (!event) return null;

  const cfg = EVENT_CONFIG[event.event_type] || EVENT_CONFIG.deforestation;
  const sev = SEVERITY_CONFIG[event.severity] || SEVERITY_CONFIG.medium;

  const fields = [
    { label: "CONFIDENCE",  value: `${(event.confidence * 100).toFixed(0)}%` },
    { label: "AREA",        value: formatArea(event.area_hectares) },
    { label: "NDVI DELTA",  value: event.ndvi_delta?.toFixed(3) ?? "—" },
    { label: "COORDS",      value: `${event.lat?.toFixed(3)}, ${event.lon?.toFixed(3)}` },
    { label: "SATELLITE",   value: event.satellite },
    { label: "DETECTED",    value: timeAgo(event.timestamp) },
  ];

  return (
    <div style={{
      background: "rgba(5,14,30,0.92)",
      border: `1px solid ${cfg.color}40`,
      borderRadius: 8, padding: 14,
      animation: "slideIn 0.3s ease",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 24 }}>{cfg.icon}</span>
          <div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 15, color: "#fff" }}>
              {cfg.label} Detected
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", letterSpacing: 1, marginTop: 2 }}>
              {event.region} · {event.tile_id}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{
            display: "inline-block", padding: "3px 10px", borderRadius: 5,
            fontSize: 10, letterSpacing: 1, textTransform: "uppercase",
            background: `${sev.color}20`, color: sev.color,
            border: `1px solid ${sev.color}40`,
          }}>
            {event.severity}
          </span>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "rgba(255,255,255,0.3)", cursor: "pointer", fontSize: 20, lineHeight: 1 }}
          >×</button>
        </div>
      </div>

      {/* Description */}
      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.55)", marginBottom: 12, lineHeight: 1.6, padding: "8px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
        {event.description}
      </div>

      {/* Field grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        {fields.map(({ label, value }) => (
          <div key={label} style={{ background: "rgba(255,255,255,0.03)", borderRadius: 6, padding: "8px 10px" }}>
            <div style={{ fontSize: 9, color: "rgba(255,255,255,0.3)", letterSpacing: 1.5, marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
