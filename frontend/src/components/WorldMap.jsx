// components/WorldMap.jsx
import { useEffect, useRef, useState, useCallback } from "react";
import { latToY, lonToX, drawMapGrid, findNearestEvent } from "../utils/geoUtils";
import { EVENT_CONFIG, SEVERITY_CONFIG } from "../utils/eventConfig";

export default function WorldMap({ events, selectedEvent, onSelect }) {
  const canvasRef  = useRef(null);
  const [hovered, setHovered] = useState(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const { width: w, height: h } = canvas;

    drawMapGrid(ctx, w, h);

    // Draw event dots
    events.forEach((evt) => {
      const x    = lonToX(evt.lon, w);
      const y    = latToY(evt.lat, h);
      const cfg  = EVENT_CONFIG[evt.event_type] || EVENT_CONFIG.deforestation;
      const isSel = selectedEvent?.event_id === evt.event_id;
      const isHov = hovered?.event_id === evt.event_id;
      const r    = isSel ? 8 : isHov ? 6 : 4.5;

      // Pulse halo for critical
      if (evt.severity === "critical") {
        ctx.beginPath();
        ctx.arc(x, y, isSel ? 18 : 12, 0, Math.PI * 2);
        ctx.fillStyle = `${cfg.color}15`;
        ctx.fill();
      }

      // Dot
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = isSel ? "#ffffff" : cfg.color;
      ctx.fill();

      // Selection ring
      if (isSel) {
        ctx.beginPath();
        ctx.arc(x, y, 11, 0, Math.PI * 2);
        ctx.strokeStyle = cfg.color;
        ctx.lineWidth   = 2;
        ctx.stroke();
      }
    });

    // Overlay label for canvas watermark
    ctx.font      = "10px monospace";
    ctx.fillStyle = "rgba(255,255,255,0.2)";
    ctx.fillText("LIVE · PATHWAY KNOWLEDGE GRAPH", 12, 18);
  }, [events, selectedEvent, hovered]);

  useEffect(() => { draw(); }, [draw]);

  const handleClick = useCallback((e) => {
    const canvas = canvasRef.current;
    const rect   = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (canvas.width  / rect.width);
    const my = (e.clientY - rect.top)  * (canvas.height / rect.height);
    const nearest = findNearestEvent(mx, my, events, canvas.width, canvas.height);
    if (nearest) onSelect(nearest);
  }, [events, onSelect]);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    const rect   = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (canvas.width  / rect.width);
    const my = (e.clientY - rect.top)  * (canvas.height / rect.height);
    setHovered(findNearestEvent(mx, my, events, canvas.width, canvas.height, 16));
  }, [events]);

  return (
    <div style={{ position: "relative", borderRadius: 8, overflow: "hidden", border: "1px solid rgba(255,255,255,0.06)" }}>
      <canvas
        ref={canvasRef}
        width={720}
        height={330}
        style={{ width: "100%", display: "block", cursor: "crosshair" }}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHovered(null)}
      />
    </div>
  );
}
