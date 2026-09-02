// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal(mean, sd) {
  const u1 = 1 - lcg();
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}

const groups = [
  { name: "Placebo", mean: 620, sd: 90, n: 400 },
  { name: "Low dose", mean: 540, sd: 80, n: 400 },
  { name: "High dose", mean: 470, sd: 70, n: 400 },
];

// Shared bin edges across all groups so the polygons compare fairly.
const BIN_WIDTH = 40;
const BIN_MIN = 250;
const BIN_MAX = 850;
const binEdges = [];
for (let edge = BIN_MIN; edge <= BIN_MAX; edge += BIN_WIDTH) binEdges.push(edge);
const binCount = binEdges.length - 1;
const binMidpoints = Array.from(
  { length: binCount },
  (_, i) => (binEdges[i] + binEdges[i + 1]) / 2,
);

function frequencyPolygon(mean, sd, n) {
  const counts = new Array(binCount).fill(0);
  for (let i = 0; i < n; i++) {
    const v = randNormal(mean, sd);
    const bin = Math.floor((v - BIN_MIN) / BIN_WIDTH);
    if (bin >= 0 && bin < binCount) counts[bin] += 1;
  }
  // Extend the polygon to zero at both ends by padding one empty bin on each side.
  const midpoints = [binMidpoints[0] - BIN_WIDTH, ...binMidpoints, binMidpoints[binCount - 1] + BIN_WIDTH];
  const values = [0, ...counts, 0];
  return midpoints.map((x, i) => [x, values[i]]);
}

// Redundant color+style encoding (spec: "distinct line colors and/or styles")
// so overlapping fills near ~530-590ms remain distinguishable by stroke alone.
const DASH_STYLES = ["Solid", "ShortDash", "ShortDot"];

const series = groups.map((g, i) => ({
  name: g.name,
  data: frequencyPolygon(g.mean, g.sd, g.n),
  color: t.palette[i],
  lineWidth: 3,
  dashStyle: DASH_STYLES[i],
  marker: { enabled: true, radius: 4, symbol: "circle", fillColor: t.palette[i], lineWidth: 0 },
  fillOpacity: 0.08,
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "frequency-polygon-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Reaction Time (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    min: BIN_MIN - BIN_WIDTH,
    max: BIN_MAX + BIN_WIDTH,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    // Distinctive Highcharts touch: mark each group's mean reaction time.
    plotLines: groups.map((g, i) => ({
      value: g.mean,
      color: t.palette[i],
      dashStyle: "Dot",
      width: 1.5,
      zIndex: 5,
      label: {
        text: `${g.name} mean`,
        rotation: 90,
        align: "left",
        x: 4,
        y: 8,
        style: { color: t.inkSoft, fontSize: "11px" },
      },
    })),
  },
  yAxis: {
    title: { text: "Frequency", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    min: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    area: { marker: { enabled: true, radius: 4 }, lineWidth: 3, fillOpacity: 0.08 },
  },
  tooltip: { enabled: false },
  series,
});
