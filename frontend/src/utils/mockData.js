// utils/mockData.js
// Generates realistic mock events when backend is offline

const REGIONS = [
  { name: "Amazon Basin",     lat: -3.4,  lon: -62.2 },
  { name: "Bangladesh Delta", lat: 23.7,  lon:  90.4 },
  { name: "Punjab Farmlands", lat: 30.9,  lon:  75.8 },
  { name: "Jakarta Suburbs",  lat: -6.2,  lon: 106.8 },
  { name: "Siberia Boreal",   lat: 60.5,  lon:  90.1 },
  { name: "Sahel Region",     lat: 13.5,  lon:   2.1 },
];

const EVENT_TYPES  = ["deforestation", "flood", "crop_stress", "construction", "fire"];
const SEVERITIES   = ["low", "medium", "high", "critical"];
const SATELLITES   = ["Sentinel-2", "Landsat-8"];

export function generateMockEvents(n = 30) {
  return Array.from({ length: n }, (_, i) => {
    const region   = REGIONS[Math.floor(Math.random() * REGIONS.length)];
    const type     = EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)];
    const severity = SEVERITIES[Math.floor(Math.random() * SEVERITIES.length)];
    return {
      event_id:      `EVT_${Math.random().toString(36).substr(2,8).toUpperCase()}`,
      event_type:    type,
      region:        region.name,
      lat:           region.lat + (Math.random() - 0.5),
      lon:           region.lon + (Math.random() - 0.5),
      severity,
      confidence:    0.65 + Math.random() * 0.32,
      area_hectares: Math.round(Math.random() * 2000 + 10),
      ndvi_delta:    -(Math.random() * 0.5),
      satellite:     SATELLITES[Math.floor(Math.random() * SATELLITES.length)],
      timestamp:     Date.now() - Math.floor(Math.random() * 7_200_000),
      tile_id:       `TILE_${Math.random().toString(36).substr(2,6).toUpperCase()}`,
      description:   `${type.replace("_"," ")} signal detected in ${region.name}.`,
    };
  });
}
