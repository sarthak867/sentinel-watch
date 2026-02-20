// components/EventFeed.jsx
import { EVENT_CONFIG, SEVERITY_CONFIG } from "../utils/eventConfig";
import { timeAgo, formatArea } from "../utils/geoUtils";

export default function EventFeed({ feed, onSelect }) {
  if (!feed.length) {
    return (
      <div style={{ padding: "20px 16px", color: "rgba(255,255,255,0.2)", fontSize: 11, textAlign: "center" }}>
        Awaiting stream...
      </div>
    );
  }

  return (
    <div style={{ overflow: "auto", flex: 1, padding: "0 16px 16px" }}>
      {feed.slice(0, 20).map((evt, i) => {
        const cfg = EVENT_CONFIG[evt.event_type] || EVENT_CONFIG.deforestation;
        return (
          <div
            key={evt.event_id}
            onClick={() => onSelect(evt)}
            style={{
              display: "flex", gap: 8, alignItems: "flex-start",
              padding: "7px 0",
              borderBottom: "1px solid rgba(255,255,255,0.04)",
              cursor: "pointer",
              opacity: Math.max(0.35, 1 - i * 0.035),
              animation: i === 0 ? "slideIn 0.35s ease" : "none",
            }}
          >
            <span style={{ fontSize: 15, flexShrink: 0, marginTop: 1 }}>{cfg.icon}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: cfg.color }}>{cfg.label}</span>
                <span style={{ fontSize: 9, color: SEVERITY_CONFIG[evt.severity]?.color || "#fff" }}>
                  {evt.severity?.toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.38)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {evt.region}
              </div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,0.2)", marginTop: 1 }}>
                {(evt.confidence * 100).toFixed(0)}% conf
                {evt.area_hectares ? ` · ${formatArea(evt.area_hectares)}` : ""}
                {" · "}{timeAgo(evt.timestamp)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
