// anyplot.ai
// scatter-map-geographic: Scatter Map with Geographic Points
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Synthetic earthquake epicenters traced along the Alpide seismic belt
// (Iberia -> Anatolia -> Himalaya -> Sunda arc). Only the core Highcharts
// bundle is loaded (no highmaps module), so geographic context comes from a
// longitude/latitude graticule rather than rendered country boundaries.
function lcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (1103515245 * s + 12345) >>> 0;
    return s / 4294967296;
  };
}
const rand = lcg(42);

const ANCHORS = [
  { lon: -9, lat: 38, depth: 20 }, // Iberia
  { lon: 14, lat: 41, depth: 15 }, // Italy
  { lon: 29, lat: 39, depth: 25 }, // Anatolia
  { lon: 48, lat: 34, depth: 35 }, // Zagros
  { lon: 71, lat: 33, depth: 70 }, // Hindu Kush
  { lon: 85, lat: 28, depth: 20 }, // Himalaya
  { lon: 96, lat: 21, depth: 90 }, // Myanmar arc
  { lon: 106, lat: 2, depth: 160 }, // Sumatra
  { lon: 120, lat: -6, depth: 210 }, // Java-Banda
  { lon: 135, lat: -3, depth: 280 }, // Banda deep
];

const MIN_MAG = 4.0;
const MAX_MAG = 7.8;
const MIN_DEPTH = 5;
const MAX_DEPTH = 300;
const POINT_COUNT = 170;

const epicenters = [];
for (let i = 0; i < POINT_COUNT; i++) {
  const along = (rand() * 0.9 + i / POINT_COUNT * 0.1 * (POINT_COUNT - 1) / POINT_COUNT) % 1;
  const span = along * (ANCHORS.length - 1);
  const idx = Math.min(Math.floor(span), ANCHORS.length - 2);
  const localT = span - idx;
  const a = ANCHORS[idx];
  const b = ANCHORS[idx + 1];

  const lonJitter = (rand() - 0.5) * 8;
  const latJitter = (rand() - 0.5) * 6;
  const depthJitter = (rand() - 0.5) * 60;

  const lon = a.lon + (b.lon - a.lon) * localT + lonJitter;
  const lat = a.lat + (b.lat - a.lat) * localT + latJitter;
  const depthBase = a.depth + (b.depth - a.depth) * localT;
  const depth = Math.min(MAX_DEPTH, Math.max(MIN_DEPTH, depthBase + depthJitter));

  // Gutenberg-Richter-like skew: many small quakes, few large ones.
  const magnitude = Math.min(MAX_MAG, MIN_MAG + -Math.log(1 - rand() * 0.98) * 0.55);

  epicenters.push({ lon, lat, magnitude, depth });
}

// --- Helpers: size + color encoding -----------------------------------------
function sizeForMagnitude(magnitude) {
  const frac = (magnitude - MIN_MAG) / (MAX_MAG - MIN_MAG);
  return 4 + frac * 16;
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function lerpColor(hexA, hexB, frac) {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  const rgb = a.map((c, i) => Math.round(c + (b[i] - c) * frac));
  return `#${rgb.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function colorForDepth(depth, alpha) {
  const frac = (depth - MIN_DEPTH) / (MAX_DEPTH - MIN_DEPTH);
  const hex = lerpColor(t.seq[0], t.seq[1], Math.min(1, Math.max(0, frac)));
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Chart -------------------------------------------------------------------
const epicenterSeries = {
  type: "scatter",
  name: "Epicenters",
  showInLegend: false,
  data: epicenters.map((e) => ({
    x: e.lon,
    y: e.lat,
    custom: { magnitude: e.magnitude, depth: e.depth },
    marker: {
      radius: sizeForMagnitude(e.magnitude),
      fillColor: colorForDepth(e.depth, 0.78),
      lineColor: t.pageBg,
      lineWidth: 1,
    },
  })),
};

// Dummy legend-only series — a standard Highcharts technique for a manual
// legend (no interactive module is required; the swatches use the exact same
// colorForDepth / sizeForMagnitude formulas the real points use).
const depthLegend = [
  { label: "Depth 5–80 km", depth: 42.5 },
  { label: "Depth 80–150 km", depth: 115 },
  { label: "Depth 150–300 km", depth: 225 },
].map((bin) => ({
  type: "scatter",
  name: bin.label,
  showInLegend: true,
  enableMouseTracking: false,
  data: [],
  marker: { radius: 9, fillColor: colorForDepth(bin.depth, 1), lineColor: t.pageBg, lineWidth: 1 },
}));

const magnitudeLegend = [
  { label: "Magnitude 4.5", magnitude: 4.5 },
  { label: "Magnitude 6.0", magnitude: 6.0 },
  { label: "Magnitude 7.5", magnitude: 7.5 },
].map((bin) => ({
  type: "scatter",
  name: bin.label,
  showInLegend: true,
  enableMouseTracking: false,
  data: [],
  marker: { radius: sizeForMagnitude(bin.magnitude), fillColor: t.palette[0], lineColor: t.pageBg, lineWidth: 1 },
}));

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    zooming: { type: "xy" }, // drag-select zoom + pan for exploring point clusters (core feature)
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "scatter-map-geographic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Alpide seismic belt · synthetic epicenters, magnitude ≥ 4.0",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -20,
    max: 145,
    tickInterval: 20,
    title: { text: "Longitude (°E)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}°" },
  },
  yAxis: {
    min: -15,
    max: 50,
    tickInterval: 10,
    startOnTick: false,
    endOnTick: false,
    title: { text: "Latitude (°N)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}°" },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolHeight: 12,
    symbolWidth: 12,
    symbolRadius: 6,
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.inkSoft,
    style: { color: t.ink, fontSize: "14px" },
    pointFormatter: function () {
      return (
        `Lon ${this.x.toFixed(1)}°, Lat ${this.y.toFixed(1)}°<br/>` +
        `Magnitude ${this.custom.magnitude.toFixed(1)}<br/>` +
        `Depth ${Math.round(this.custom.depth)} km`
      );
    },
  },
  plotOptions: {
    series: { animation: false },
    scatter: { marker: { symbol: "circle" } },
  },
  series: [epicenterSeries, ...depthLegend, ...magnitudeLegend],
});
