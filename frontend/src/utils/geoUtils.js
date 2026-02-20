// utils/geoUtils.js
// Geospatial utility functions for canvas rendering

/**
 * Convert latitude to canvas Y coordinate (equirectangular projection)
 * @param {number} lat  - latitude (-90 to 90)
 * @param {number} h    - canvas height in pixels
 */
export const latToY = (lat, h) => ((90 - lat) / 180) * h;

/**
 * Convert longitude to canvas X coordinate
 * @param {number} lon  - longitude (-180 to 180)
 * @param {number} w    - canvas width in pixels
 */
export const lonToX = (lon, w) => ((lon + 180) / 360) * w;

/**
 * Convert canvas coordinates back to lat/lon
 */
export const xyToLatLon = (x, y, w, h) => ({
  lat: 90 - (y / h) * 180,
  lon: (x / w) * 360 - 180,
});

/**
 * Find the nearest event to a canvas click
 * @param {number} mx, my  - mouse coords in canvas space
 * @param {Array}  events  - list of event objects with lat/lon
 * @param {number} w, h    - canvas dimensions
 * @param {number} maxDist - max pixel distance for hit detection
 */
export const findNearestEvent = (mx, my, events, w, h, maxDist = 18) => {
  let closest = null;
  let minDist = maxDist;

  events.forEach((evt) => {
    const x = lonToX(evt.lon, w);
    const y = latToY(evt.lat, h);
    const d = Math.hypot(mx - x, my - y);
    if (d < minDist) {
      minDist = d;
      closest = evt;
    }
  });

  return closest;
};

/**
 * Draw a world map grid on a canvas context
 * @param {CanvasRenderingContext2D} ctx
 * @param {number} w, h
 */
export const drawMapGrid = (ctx, w, h) => {
  // Background
  ctx.fillStyle = "#050a14";
  ctx.fillRect(0, 0, w, h);

  // Latitude/longitude grid lines
  ctx.strokeStyle = "rgba(255,255,255,0.04)";
  ctx.lineWidth = 1;
  for (let lat = -60; lat <= 60; lat += 30) {
    const y = latToY(lat, h);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }
  for (let lon = -150; lon <= 150; lon += 60) {
    const x = lonToX(lon, w);
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }

  // Equator (slightly brighter)
  ctx.strokeStyle = "rgba(255,255,255,0.10)";
  ctx.lineWidth = 1;
  const eqY = latToY(0, h);
  ctx.beginPath(); ctx.moveTo(0, eqY); ctx.lineTo(w, eqY); ctx.stroke();

  // Tropics (faint)
  ctx.strokeStyle = "rgba(255,200,50,0.06)";
  [23.5, -23.5].forEach((lat) => {
    const y = latToY(lat, h);
    ctx.setLineDash([4, 8]);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    ctx.setLineDash([]);
  });
};

/**
 * Format a unix timestamp to human-readable relative time
 */
export const timeAgo = (timestamp) => {
  const diff = Date.now() - timestamp;
  const mins = Math.floor(diff / 60000);
  const hrs  = Math.floor(diff / 3600000);
  if (mins < 1)   return "just now";
  if (mins < 60)  return `${mins}m ago`;
  if (hrs  < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

/**
 * Format area in hectares with appropriate unit
 */
export const formatArea = (ha) => {
  if (ha >= 100000) return `${(ha / 100000).toFixed(1)}M ha`;
  if (ha >= 1000)   return `${(ha / 1000).toFixed(1)}k ha`;
  return `${ha.toFixed(0)} ha`;
};
