// anyplot.ai
// map-connection-lines: Connection Lines Map (Origin-Destination)
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): a global hub-airport flight network --
const airports = [
  { code: "JFK", lon: -73.7781, lat: 40.6413 },
  { code: "LAX", lon: -118.4085, lat: 33.9416 },
  { code: "GRU", lon: -46.4731, lat: -23.4356 },
  { code: "LHR", lon: -0.4614, lat: 51.47 },
  { code: "FRA", lon: 8.5706, lat: 50.0379 },
  { code: "JNB", lon: 28.246, lat: -26.1392 },
  { code: "DXB", lon: 55.3644, lat: 25.2532 },
  { code: "DEL", lon: 77.1025, lat: 28.5562 },
  { code: "SIN", lon: 103.9915, lat: 1.3644 },
  { code: "HKG", lon: 113.9185, lat: 22.308 },
  { code: "HND", lon: 139.7798, lat: 35.5494 },
  { code: "SYD", lon: 151.1772, lat: -33.9399 },
];

// [origin, destination, annual passengers in thousands]
const routes = [
  ["JFK", "LHR", 2800],
  ["JFK", "FRA", 1200],
  ["JFK", "GRU", 1100],
  ["LAX", "JFK", 1000],
  ["LAX", "LHR", 1300],
  ["GRU", "LHR", 750],
  ["LHR", "DXB", 2200],
  ["LHR", "JNB", 950],
  ["FRA", "DXB", 1800],
  ["FRA", "DEL", 800],
  ["DXB", "JNB", 1300],
  ["DXB", "SIN", 2600],
  ["DXB", "HKG", 1700],
  ["DEL", "SIN", 1100],
  ["SIN", "HKG", 2400],
  ["SIN", "SYD", 1600],
  ["HKG", "HND", 1900],
  ["HND", "SYD", 1000],
];

const byCode = Object.fromEntries(airports.map((a) => [a.code, a]));
const maxPassengers = Math.max(...routes.map((r) => r[2]));

const traffic = {};
for (const [origin, dest, passengers] of routes) {
  traffic[origin] = (traffic[origin] || 0) + passengers;
  traffic[dest] = (traffic[dest] || 0) + passengers;
}

const lineData = routes.map(([origin, dest, passengers]) => {
  const share = passengers / maxPassengers;
  return {
    coords: [
      [byCode[origin].lon, byCode[origin].lat],
      [byCode[dest].lon, byCode[dest].lat],
    ],
    value: passengers,
    lineStyle: { width: 1.2 + share * 5, opacity: 0.28 + share * 0.32, curveness: 0.2 },
  };
});

const nodeData = airports.map((a) => ({
  name: a.code,
  value: [a.lon, a.lat, traffic[a.code]],
}));

// --- Init --------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------
// No offline basemap data is available to this browser-only runtime (no
// bundled world GeoJSON, no network fetch), so a longitude/latitude
// graticule stands in for coastlines/borders to give geographic context.
const title = "Global Flight Routes · map-connection-lines · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: [t.palette[0]],
  title: {
    text: title,
    subtext: "Line width & opacity scale with annual passenger volume (thousands) · marker size scales with hub traffic",
    left: "center",
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  tooltip: {
    trigger: "item",
    formatter: (p) =>
      p.seriesType === "lines" ? `${p.data.value}k passengers/yr` : `${p.name}: ${p.value[2]}k passengers`,
  },
  grid: { left: 110, right: 90, top: 190, bottom: 110, containLabel: true },
  xAxis: {
    type: "value",
    min: -180,
    max: 180,
    interval: 30,
    name: "Longitude",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      formatter: (v) => `${Math.abs(v)}°${v > 0 ? "E" : v < 0 ? "W" : ""}`,
    },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    min: -60,
    max: 80,
    interval: 30,
    name: "Latitude",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      formatter: (v) => `${Math.abs(v)}°${v > 0 ? "N" : v < 0 ? "S" : ""}`,
    },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Routes",
      type: "lines",
      coordinateSystem: "cartesian2d",
      xAxisIndex: 0,
      yAxisIndex: 0,
      symbol: ["none", "arrow"],
      symbolSize: [0, 8],
      data: lineData,
      lineStyle: { color: t.palette[0] },
      z: 2,
    },
    {
      name: "Airports",
      type: "scatter",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: nodeData,
      symbolSize: (val) => 12 + Math.sqrt(val[2]) * 0.55,
      itemStyle: { color: t.palette[0], opacity: 0.9, borderColor: t.pageBg, borderWidth: 1.5 },
      label: { show: true, formatter: "{b}", position: "top", color: t.ink, fontSize: 13, fontWeight: 500 },
      z: 3,
    },
  ],
});
