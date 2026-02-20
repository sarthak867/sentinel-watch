// components/EventGrid.jsx
import { EVENT_CONFIG, SEVERITY_CONFIG } from "../utils/eventConfig";
import { formatArea } from "../utils/geoUtils";

export default function EventGrid({ events, selectedEvent, onSelect }) {
  return (
    <div style={{ flex: 1, overflow: "auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, alignContent: "start" }}>
      {events.slice(0, 20).map((evt) => {
        const cfg   = EVENT_CONFIG[evt.event_type] || EVENT_CONFIG.deforestation;
        const isSel = selectedEvent?.event_id === evt.event_id;

        return (
          <div
            key={evt.event_id}
            onClick={() => onSelect(evt)}
            style={{
              background: isSel ? cfg.bg : "rgba(5,14,30,0.6)",
              border:     `1px solid ${isSel ? cfg.color + "60" : "rgba(255,255,255,0.06)"}`,
              borderRadius: 8, padding: "10px 12px",
              cursor: "pointer", transition: "all 0.18s",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 18 }}>{cfg.icon}</span>
              <span style={{
                display: "inline-block", padding: "2px 8px", borderRadius: 4,
                fontSize: 10, letterSpacing: 1, textTransform: "uppercase",
                background: `${SEVERITY_CONFIG[evt.severity]?.color}18`,
                color: SEVERITY_CONFIG[evt.severity]?.color,
                border: `1px solid ${SEVERITY_CONFIG[evt.severity]?.color}30`,
              }}>
                {evt.severity}
              </span>
            </div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 500, fontSize: 12, color: "#e2e8f0", marginBottom: 2 }}>
              {cfg.label}
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginBottom: 6 }}>{evt.region}</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)" }}>{evt.tile_id}</span>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: cfg.color }}>{(evt.confidence * 100).toFixed(0)}%</div>
                <div style={{ fontSize: 9, color: "rgba(255,255,255,0.2)" }}>conf</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
