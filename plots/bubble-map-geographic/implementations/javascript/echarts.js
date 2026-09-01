// anyplot.ai
// bubble-map-geographic: Bubble Map with Sized Geographic Markers
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 75/100 | Created: 2026-09-01
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// World metro-area population by city (millions, approximate), grouped by
// continent for color + legend. [longitude, latitude, population].
const REGIONS = [
  {
    name: "Asia",
    color: t.palette[0],
    cities: [
      { name: "Tokyo", lon: 139.65, lat: 35.68, pop: 37.4 },
      { name: "Delhi", lon: 77.21, lat: 28.61, pop: 32.9 },
      { name: "Shanghai", lon: 121.47, lat: 31.23, pop: 29.2 },
      { name: "Dhaka", lon: 90.41, lat: 23.81, pop: 22.5 },
      { name: "Beijing", lon: 116.41, lat: 39.9, pop: 21.9 },
      { name: "Mumbai", lon: 72.88, lat: 19.08, pop: 21.3 },
      { name: "Osaka", lon: 135.5, lat: 34.69, pop: 19.1 },
      { name: "Karachi", lon: 67.01, lat: 24.86, pop: 16.8 },
    ],
  },
  {
    name: "Africa",
    color: t.palette[1],
    cities: [
      { name: "Cairo", lon: 31.24, lat: 30.04, pop: 22.2 },
      { name: "Kinshasa", lon: 15.27, lat: -4.44, pop: 15.6 },
      { name: "Lagos", lon: 3.38, lat: 6.52, pop: 15.4 },
    ],
  },
  {
    name: "Europe",
    color: t.palette[2],
    cities: [
      { name: "Istanbul", lon: 28.97, lat: 41.01, pop: 15.6 },
      { name: "Moscow", lon: 37.62, lat: 55.75, pop: 12.6 },
      { name: "Paris", lon: 2.35, lat: 48.85, pop: 11.1 },
      { name: "London", lon: -0.13, lat: 51.51, pop: 9.6 },
    ],
  },
  {
    name: "N. America",
    color: t.palette[3],
    cities: [
      { name: "Mexico City", lon: -99.13, lat: 19.43, pop: 22.3 },
      { name: "New York", lon: -74.01, lat: 40.71, pop: 18.9 },
      { name: "Los Angeles", lon: -118.24, lat: 34.05, pop: 12.5 },
    ],
  },
  {
    name: "S. America",
    color: t.palette[4],
    cities: [
      { name: "Sao Paulo", lon: -46.63, lat: -23.55, pop: 22.6 },
      { name: "Buenos Aires", lon: -58.38, lat: -34.6, pop: 15.4 },
      { name: "Rio de Janeiro", lon: -43.17, lat: -22.91, pop: 13.7 },
    ],
  },
  {
    name: "Oceania",
    color: t.palette[5],
    cities: [
      { name: "Sydney", lon: 151.21, lat: -33.87, pop: 5.3 },
      { name: "Melbourne", lon: 144.96, lat: -37.81, pop: 5.2 },
    ],
  },
];

// --- Basemap: simplified world continent outlines (rough, low-vertex hand
// trace -- geographic context only, not a precise survey boundary) ----------
const NORTH_AMERICA = [
  [-165, 68], [-150, 60], [-130, 55], [-125, 48], [-124, 40], [-118, 34],
  [-108, 23], [-97, 16], [-90, 14], [-84, 9], [-77, 8], [-82, 22], [-80, 31],
  [-75, 35], [-71, 41], [-66, 45], [-60, 48], [-55, 52], [-65, 58], [-80, 62],
  [-95, 68], [-110, 72], [-130, 71], [-150, 71], [-165, 68],
];
const SOUTH_AMERICA = [
  [-77, 8], [-79, 1], [-81, -5], [-81, -15], [-75, -20], [-71, -30],
  [-71, -40], [-73, -50], [-68, -55], [-65, -52], [-62, -42], [-58, -34],
  [-48, -25], [-40, -12], [-50, 0], [-60, 5], [-65, 8], [-77, 8],
];
const AFRICA = [
  [-17, 15], [-16, 21], [-10, 30], [0, 37], [10, 37], [20, 32], [32, 31],
  [35, 27], [43, 13], [51, 12], [45, 0], [40, -12], [35, -20], [33, -27],
  [27, -33], [18, -34], [14, -23], [12, -6], [9, 4], [-5, 5], [-11, 7],
  [-17, 15],
];
const EURASIA = [
  [-9, 37], [-9, 44], [-5, 48], [3, 51], [10, 60], [25, 70], [40, 68],
  [60, 72], [90, 75], [130, 75], [170, 66], [160, 55], [140, 45], [130, 35],
  [122, 30], [108, 10], [100, 5], [95, 15], [88, 22], [80, 10], [77, 8],
  [70, 20], [65, 25], [55, 27], [50, 15], [35, 15], [35, 32], [28, 36],
  [23, 37], [12, 38], [-5, 36], [-9, 37],
];
const AUSTRALIA = [
  [113, -22], [114, -30], [121, -34], [130, -32], [137, -35], [141, -38],
  [147, -38], [150, -37], [153, -28], [145, -17], [142, -11], [136, -12],
  [130, -12], [124, -15], [113, -22],
];
const CONTINENTS = [NORTH_AMERICA, SOUTH_AMERICA, AFRICA, EURASIA, AUSTRALIA];

// Fills+outlines one continent polygon; coordinates are projected through the
// chart's own lon/lat value axes via api.coord (same cartesian2d technique
// used for the coastline/ocean layer in hexbin-map-geographic).
function makeLandRenderer(coords) {
  return function renderLand(params, api) {
    const points = coords.map(([lon, lat]) => api.coord([lon, lat]));
    return {
      type: "polygon",
      shape: { points },
      style: { fill: t.grid, stroke: t.inkSoft, lineWidth: 1, opacity: 0.55 },
      silent: true,
    };
  };
}

const ALL_POPS = REGIONS.flatMap((r) => r.cities.map((c) => c.pop));
const POP_MIN = Math.min(...ALL_POPS);
const POP_MAX = Math.max(...ALL_POPS);
const SIZE_MIN = 24;
const SIZE_MAX = 78;

// Bubble diameter scales with sqrt(value) so bubble AREA — not radius — is
// proportional to population, per anyplot's bubble-map perception rule.
function bubbleSize(pop) {
  const s0 = Math.sqrt(POP_MIN);
  const s1 = Math.sqrt(POP_MAX);
  const ratio = Math.max(0, Math.min(1, (Math.sqrt(pop) - s0) / (s1 - s0)));
  return SIZE_MIN + ratio * (SIZE_MAX - SIZE_MIN);
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Size-key legend (fixed screen-space graphic, stacked top-to-bottom) ---
const LEGEND_VALUES = [37, 15, 5];
const LEGEND_X = 1480;
const legendGraphics = [
  {
    type: "text",
    left: LEGEND_X - 30,
    top: 232,
    style: { text: "Population (M)", fill: t.inkSoft, fontSize: 13, fontWeight: 500 },
  },
];
let cy = 260;
for (const v of LEGEND_VALUES) {
  const r = bubbleSize(v) / 2;
  cy += r;
  legendGraphics.push({
    type: "circle",
    shape: { cx: LEGEND_X, cy, r },
    style: { fill: "none", stroke: t.inkSoft, lineWidth: 1.5 },
  });
  legendGraphics.push({
    type: "text",
    left: LEGEND_X + r + 14,
    top: cy - 7,
    style: { text: `${v}M`, fill: t.inkSoft, fontSize: 13 },
  });
  cy += r + 24;
}

// --- Option -----------------------------------------------------------------
const title = "World City Populations · bubble-map-geographic · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 18, fontWeight: 500 },
  },
  legend: {
    top: 74,
    data: REGIONS.map((r) => r.name),
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 16,
    itemHeight: 12,
  },
  tooltip: {
    trigger: "item",
    formatter: (p) => `${p.data.name}<br/>${p.data.value[2]}M metro population`,
  },
  grid: { left: 90, top: 150, width: 1300, height: 560 },
  xAxis: {
    type: "value",
    name: "Longitude",
    nameLocation: "middle",
    nameGap: 34,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: -180,
    max: 180,
    interval: 30,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 12,
      formatter: (v) => `${Math.abs(v)}°${v < 0 ? "W" : v > 0 ? "E" : ""}`,
    },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Latitude",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: -60,
    max: 80,
    interval: 30,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 12,
      formatter: (v) => `${Math.abs(v)}°${v < 0 ? "S" : v > 0 ? "N" : ""}`,
    },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  graphic: legendGraphics,
  series: [
    ...CONTINENTS.map((coords, i) => ({
      name: `Basemap ${i}`,
      type: "custom",
      coordinateSystem: "cartesian2d",
      renderItem: makeLandRenderer(coords),
      data: [[0, 0]],
      silent: true,
      tooltip: { show: false },
      z: 0,
    })),
    ...REGIONS.map((region, i) => ({
      name: region.name,
      type: "scatter",
      data: region.cities.map((c) => ({ name: c.name, value: [c.lon, c.lat, c.pop] })),
      symbolSize: (val) => bubbleSize(val[2]),
      itemStyle: { color: region.color, opacity: 0.58, borderColor: t.pageBg, borderWidth: 1 },
      emphasis: { itemStyle: { opacity: 0.9 } },
      z: 2,
      ...(i === 0
        ? {
            markLine: {
              silent: true,
              symbol: "none",
              lineStyle: { color: t.ink, opacity: 0.2, type: "dashed", width: 1 },
              label: { show: false },
              data: [{ xAxis: 0 }, { yAxis: 0 }],
            },
          }
        : {}),
    })),
  ],
});
