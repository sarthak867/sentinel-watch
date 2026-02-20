// components/NDVISparkline.jsx
// Tiny SVG sparkline showing NDVI trend for an event tile

export default function NDVISparkline({ currentNdvi = 0.5, baseline = 0.55, width = 80, height = 28 }) {
  const w = width, h = height;
  const totalPoints = 20;

  // Generate a simulated time series ending at currentNdvi
  const points = Array.from({ length: totalPoints }, (_, i) => {
    const progress   = i / (totalPoints - 1);
    const noise      = Math.sin(i * 1.7) * 0.04 + Math.sin(i * 0.4) * 0.03;
    const transition = i >= 14
      ? baseline + (currentNdvi - baseline) * ((i - 14) / (totalPoints - 14))
      : baseline;
    const val = transition + noise;
    const x = (i / (totalPoints - 1)) * w;
    const y = h - ((Math.max(-0.2, Math.min(1.0, val)) + 0.2) / 1.2) * h;
    return `${x.toFixed(1)},${Math.max(1, Math.min(h - 1, y)).toFixed(1)}`;
  });

  const delta = currentNdvi - baseline;
  const color = delta > -0.1 ? "#22c55e" : delta > -0.25 ? "#f59e0b" : "#ef4444";

  // Baseline reference line
  const baselineY = h - ((baseline + 0.2) / 1.2) * h;

  return (
    <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
      {/* Baseline reference */}
      <line
        x1={w * 0.7} y1={baselineY} x2={w} y2={baselineY}
        stroke={color} strokeWidth="1" strokeDasharray="2,3" opacity="0.3"
      />
      {/* NDVI sparkline */}
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        opacity="0.85"
      />
      {/* End dot */}
      <circle
        cx={w}
        cy={parseFloat(points[totalPoints - 1].split(",")[1])}
        r="2"
        fill={color}
      />
    </svg>
  );
}
