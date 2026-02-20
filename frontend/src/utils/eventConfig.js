// utils/eventConfig.js
// Centralized config for all event types — used by every component

export const EVENT_CONFIG = {
  deforestation: {
    icon: "🌳",
    label: "Deforestation",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
    border: "#166534",
    description: "Sudden NDVI drop below forest baseline",
  },
  flood: {
    icon: "🌊",
    label: "Flood",
    color: "#38bdf8",
    bg: "rgba(56,189,248,0.12)",
    border: "#0369a1",
    description: "NDWI surge above seasonal water baseline",
  },
  crop_stress: {
    icon: "🌾",
    label: "Crop Stress",
    color: "#fbbf24",
    bg: "rgba(251,191,36,0.12)",
    border: "#92400e",
    description: "Moderate NDVI decline in agricultural zones",
  },
  construction: {
    icon: "🏗️",
    label: "Construction",
    color: "#a78bfa",
    bg: "rgba(167,139,250,0.12)",
    border: "#4c1d95",
    description: "NDVI drop + high SWIR reflectance",
  },
  fire: {
    icon: "🔥",
    label: "Fire",
    color: "#fb923c",
    bg: "rgba(251,146,60,0.12)",
    border: "#7c2d12",
    description: "SWIR spike + near-zero NDVI",
  },
  drought: {
    icon: "🏜️",
    label: "Drought",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.12)",
    border: "#78350f",
    description: "Negative NDWI delta — water body shrinkage",
  },
};

export const SEVERITY_CONFIG = {
  critical: { color: "#ef4444", rank: 4, label: "Critical" },
  high:     { color: "#f97316", rank: 3, label: "High"     },
  medium:   { color: "#eab308", rank: 2, label: "Medium"   },
  low:      { color: "#22c55e", rank: 1, label: "Low"      },
};

export const PIPELINE_STAGES = [
  { label: "Tile Ingestion",         status: "active"  },
  { label: "NDVI/NDWI Compute",      status: "active"  },
  { label: "Change Detection UDF",   status: "active"  },
  { label: "Vision Model (GPT-4V)",  status: "standby" },
  { label: "Knowledge Graph Write",  status: "active"  },
  { label: "Alert Broadcast",        status: "active"  },
];

export const SATELLITE_COLORS = {
  "Sentinel-2": "#38bdf8",
  "Landsat-8":  "#a78bfa",
};
