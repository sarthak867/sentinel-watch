// components/BreakdownBars.jsx
import { EVENT_CONFIG } from "../utils/eventConfig";

export default function BreakdownBars({ events }) {
  const total = events.length || 1;
  const counts = Object.keys(EVENT_CONFIG).reduce((acc, type) => {
    acc[type] = events.filter((e) => e.event_type === type).length;
    return acc;
  }, {});

  return (
    <div>
      {Object.entries(EVENT_CONFIG).map(([type, cfg]) => {
        const count = counts[type] || 0;
        const pct   = Math.round((count / total) * 100);

        return (
          <div key={type} style={{ marginBottom: 9 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", display: "flex", alignItems: "center", gap: 5 }}>
                <span>{cfg.icon}</span>
                {cfg.label}
              </span>
              <span style={{ fontSize: 11, fontWeight: 600, color: cfg.color }}>{count}</span>
            </div>
            <div style={{ height: 3, background: "rgba(255,255,255,0.06)", borderRadius: 2 }}>
              <div style={{
                width:  `${pct}%`,
                height: "100%",
                background: cfg.color,
                borderRadius: 2,
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
