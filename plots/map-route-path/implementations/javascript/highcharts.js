// anyplot.ai
// map-route-path: Route Path Map
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: a hiking trail GPS track (in-memory, deterministic) -------------
// Small LCG so the meander is reproducible without a network-fetched track.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (1103515245 * state + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const rand = lcg(42);

const WAYPOINTS = 140;
const START_LAT = 40.3428; // Bear Lake trailhead, Rocky Mountain National Park
const START_LON = -105.6836;
const BASE_BEARING_DEG = 55; // roughly north-east climb toward the summit

const path = [];
let lat = START_LAT;
let lon = START_LON;
for (let i = 0; i < WAYPOINTS; i++) {
  const progress = i / (WAYPOINTS - 1);
  const meanderDeg = Math.sin(progress * Math.PI * 5.5) * 55 + (rand() - 0.5) * 30;
  const bearing = ((BASE_BEARING_DEG + meanderDeg) * Math.PI) / 180;
  const stepKm = 0.045 + rand() * 0.02;
  path.push({ lat, lon, sequence: i });
  lat += (stepKm / 111) * Math.cos(bearing);
  lon += (stepKm / (111 * Math.cos((lat * Math.PI) / 180))) * Math.sin(bearing);
}

// --- Color gradient along the path (elapsed time: seq[0] -> seq[1]) --------
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function interpolateHex(hexA, hexB, frac) {
  const [ar, ag, ab] = hexToRgb(hexA);
  const [br, bg, bb] = hexToRgb(hexB);
  const mix = (a, b) => Math.round(a + (b - a) * frac);
  return `rgb(${mix(ar, br)}, ${mix(ag, bg)}, ${mix(ab, bb)})`;
}

const SEGMENTS = 9;
const pathSegments = [];
for (let s = 0; s < SEGMENTS; s++) {
  const startIdx = Math.floor((s * (WAYPOINTS - 1)) / SEGMENTS);
  const endIdx = Math.floor(((s + 1) * (WAYPOINTS - 1)) / SEGMENTS);
  pathSegments.push({
    type: "line",
    name: `Segment ${s}`,
    data: path.slice(startIdx, endIdx + 1).map((p) => [p.lon, p.lat]),
    color: interpolateHex(t.seq[0], t.seq[1], s / (SEGMENTS - 1)),
    lineWidth: 3.5,
    marker: { enabled: false, states: { hover: { enabled: true, radius: 5 } } },
    enableMouseTracking: true,
    showInLegend: false,
  });
}

const start = path[0];
const finish = path[path.length - 1];

// --- Chart -------------------------------------------------------------------
const title = "Hiking Trail GPS Track · map-route-path · javascript · highcharts · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));

Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    zoomType: "xy",
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: title,
    style: { color: t.ink, fontSize: `${titleFontSize}px`, fontWeight: "600" },
  },
  subtitle: {
    text: "Line color traces elapsed time from start (green) to finish (blue) · drag to zoom",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Longitude (°)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value:.3f}" },
  },
  yAxis: {
    title: { text: "Latitude (°)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value:.3f}" },
  },
  tooltip: {
    formatter() {
      return `Waypoint ${this.point.index}<br/>Lon: ${this.x.toFixed(4)}°<br/>Lat: ${this.y.toFixed(4)}°`;
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
  },
  series: [
    ...pathSegments,
    {
      type: "scatter",
      name: "Start",
      data: [{ x: start.lon, y: start.lat }],
      color: t.palette[0],
      marker: { symbol: "circle", radius: 11, lineColor: t.pageBg, lineWidth: 2 },
      dataLabels: {
        enabled: true,
        format: "Start",
        y: -18,
        style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
      },
      showInLegend: true,
    },
    {
      type: "scatter",
      name: "Finish",
      data: [{ x: finish.lon, y: finish.lat }],
      color: "#AE3030",
      marker: { symbol: "square", radius: 10, lineColor: t.pageBg, lineWidth: 2 },
      dataLabels: {
        enabled: true,
        format: "Finish",
        y: -18,
        style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
      },
      showInLegend: true,
    },
  ],
});
