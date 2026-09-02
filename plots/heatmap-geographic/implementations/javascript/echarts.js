// anyplot.ai
// heatmap-geographic: Geographic Heatmap for Spatial Density
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 78/100 | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic retail-visit pings across San Francisco ---------------
// Fixed-seed LCG (no seeded Math.random in the browser)
function makeLcg(seed) {
  let state = seed >>> 0;
  return function rng() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeLcg(42);

function gaussian(mean, std) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

// Neighborhood clusters: center coord, point count, spread, visit-weight range
// Downtown/Mission spread is tightened to well under half their ~1.9km
// separation so the KDE shows a visible valley between the two peaks instead
// of merging into one region.
const neighborhoods = [
  { name: "Downtown", lon: -122.4194, lat: 37.7749, n: 700, lonStd: 0.006, latStd: 0.005, weightMean: 62, weightStd: 20 },
  { name: "Mission", lon: -122.4090, lat: 37.7599, n: 600, lonStd: 0.006, latStd: 0.005, weightMean: 50, weightStd: 18 },
  { name: "Sunset", lon: -122.4862, lat: 37.7599, n: 500, lonStd: 0.007, latStd: 0.006, weightMean: 40, weightStd: 15 },
];

const points = [];
neighborhoods.forEach((c) => {
  for (let i = 0; i < c.n; i++) {
    points.push({
      lon: gaussian(c.lon, c.lonStd),
      lat: gaussian(c.lat, c.latStd),
      weight: Math.max(5, gaussian(c.weightMean, c.weightStd)),
    });
  }
});

// --- Kernel density estimation onto a lon/lat grid --------------------------
const lonMin = -122.52, lonMax = -122.375;
const latMin = 37.735, latMax = 37.805;
const nx = 42, ny = 38;
const bandwidthLon = 0.0035, bandwidthLat = 0.003;

const cellLon = (i) => lonMin + ((lonMax - lonMin) * i) / (nx - 1);
const cellLat = (j) => latMin + ((latMax - latMin) * j) / (ny - 1);
const lonIndexF = (lon) => ((lon - lonMin) / (lonMax - lonMin)) * (nx - 1);
const latIndexF = (lat) => ((lat - latMin) / (latMax - latMin)) * (ny - 1);

const grid = [];
let minDensity = Infinity;
let maxDensity = 0;
for (let i = 0; i < nx; i++) {
  const lon = cellLon(i);
  for (let j = 0; j < ny; j++) {
    const lat = cellLat(j);
    let density = 0;
    for (const p of points) {
      const dLon = (lon - p.lon) / bandwidthLon;
      const dLat = (lat - p.lat) / bandwidthLat;
      density += p.weight * Math.exp(-0.5 * (dLon * dLon + dLat * dLat));
    }
    // sqrt compresses the KDE's long right tail so mid/low density cells stay
    // visually distinguishable instead of washing out near the global peak
    const scaled = Math.sqrt(density);
    grid.push([i, j, scaled]);
    if (scaled > maxDensity) maxDensity = scaled;
    if (scaled < minDensity) minDensity = scaled;
  }
}

const lonIndex = (lon) => Math.round(((lon - lonMin) / (lonMax - lonMin)) * (nx - 1));
const latIndex = (lat) => Math.round(((lat - latMin) / (latMax - latMin)) * (ny - 1));
const markers = neighborhoods.map((c) => ({
  value: [lonIndex(c.lon), latIndex(c.lat)],
  name: c.name,
}));

const lonLabels = Array.from({ length: nx }, (_, i) => cellLon(i).toFixed(2));
const latLabels = Array.from({ length: ny }, (_, j) => cellLat(j).toFixed(2));

// Simplified San Francisco shoreline (Ocean Beach -> Golden Gate -> northern
// waterfront -> Bay side), hand-picked lon/lat vertices anchoring the density
// grid to real geography.
const coastlinePoints = [
  [-122.5090, 37.736],
  [-122.5110, 37.752],
  [-122.5115, 37.768],
  [-122.5095, 37.784],
  [-122.5010, 37.797],
  [-122.4830, 37.804],
  [-122.4520, 37.805],
  [-122.4250, 37.804],
  [-122.4040, 37.799],
  [-122.3910, 37.789],
  [-122.3855, 37.774],
  [-122.3800, 37.758],
  [-122.3770, 37.742],
].map(([lon, lat]) => [lonIndexF(lon), latIndexF(lat)]);

// --- Title (fontsize scales down for the descriptive prefix) ---------------
const title = "San Francisco Retail Visits · heatmap-geographic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 16,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  grid: { left: 90, right: 40, top: 110, bottom: 190 },
  xAxis: {
    type: "category",
    data: lonLabels,
    name: "Longitude",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 12, interval: 6, rotate: 45 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  yAxis: {
    type: "category",
    data: latLabels,
    name: "Latitude",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 12, interval: 6 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  visualMap: {
    type: "continuous",
    min: minDensity,
    max: maxDensity,
    calculable: false,
    orient: "horizontal",
    left: "center",
    bottom: 30,
    itemWidth: 16,
    itemHeight: 220,
    text: ["High visit density", "Low"],
    textStyle: { color: t.inkSoft, fontSize: 12 },
    inRange: { color: t.seq },
  },
  dataZoom: [
    { type: "inside", xAxisIndex: 0 },
    { type: "inside", yAxisIndex: 0 },
  ],
  series: [
    {
      name: "Visit density",
      type: "heatmap",
      coordinateSystem: "cartesian2d",
      data: grid,
      progressive: 0,
      itemStyle: { borderWidth: 0 },
    },
    {
      // Drawn above the heatmap (not literally "underneath") because the heatmap
      // paints every cell opaquely, including low-density cells at the ramp's
      // base color, so a layer beneath it would be fully hidden.
      name: "Coastline",
      type: "line",
      coordinateSystem: "cartesian2d",
      data: coastlinePoints,
      showSymbol: false,
      smooth: 0.3,
      lineStyle: { color: t.inkSoft, width: 2, type: "dashed", opacity: 0.6 },
      z: 5,
      silent: true,
      tooltip: { show: false },
    },
    {
      name: "Neighborhood",
      type: "scatter",
      data: markers,
      symbolSize: 7,
      itemStyle: { color: t.ink, opacity: 0.6 },
      label: {
        show: true,
        formatter: "{b}",
        position: "top",
        color: t.ink,
        fontSize: 13,
        fontWeight: 500,
      },
      z: 10,
      tooltip: { show: false },
    },
  ],
});
