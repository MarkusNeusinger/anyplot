// anyplot.ai
// heatmap-stripes-climate: Climate Warming Stripes
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Synthetic global-mean temperature anomaly, 1850-2024, relative to a
// 1961-1990 baseline. An accelerating warming trend plus small year-to-year
// noise from a fixed-seed LCG (the browser has no seeded Math.random).
let seed = 42;
const lcgRandom = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

const startYear = 1850;
const endYear = 2024;
const years = [];
for (let year = startYear; year <= endYear; year += 1) years.push(year);

const anomalies = years.map((year) => {
  const progress = (year - startYear) / (endYear - startYear);
  const trend = -0.45 + 1.65 * Math.pow(progress, 1.8);
  const noise = (lcgRandom() - 0.5) * 0.3;
  return Math.round((trend + noise) * 100) / 100;
});

// Symmetric color scale around zero so equal +/- anomalies match in intensity.
// Domain convention (see style guide "Semantic exception"): cold -> blue,
// warm -> red, so the diverging stops are used in reverse order (t.div is
// [red, neutral, blue]).
const maxAbsAnomaly = Math.max(...anomalies.map(Math.abs));

const hexToRgb = (hex) => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
];
const rgbToHex = (rgb) =>
  `#${rgb.map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")}`;
const lerpColor = (colorA, colorB, ratio) => {
  const a = hexToRgb(colorA);
  const b = hexToRgb(colorB);
  return rgbToHex(a.map((v, i) => v + (b[i] - v) * ratio));
};

// column series has no built-in colorAxis coloring (that composition ships
// only with the heatmap/treemap modules, which are not loaded), so each
// bar's color is computed directly from the diverging Imprint stops.
const colorForAnomaly = (value) => {
  const cold = t.div[2];
  const neutral = t.div[1];
  const warm = t.div[0];
  const u = 0.5 + value / (2 * maxAbsAnomaly);
  return u < 0.5 ? lerpColor(cold, neutral, u / 0.5) : lerpColor(neutral, warm, (u - 0.5) / 0.5);
};

const stripes = years.map((year, i) => ({
  x: i,
  y: 1,
  color: colorForAnomaly(anomalies[i]),
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    spacing: [40, 0, 0, 0],
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "heatmap-stripes-climate · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    visible: false,
    min: 0,
    max: years.length - 1,
    minPadding: 0,
    maxPadding: 0,
  },
  yAxis: {
    visible: false,
    min: 0,
    max: 1,
    minPadding: 0,
    maxPadding: 0,
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    column: {
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 0,
    },
  },
  series: [
    {
      name: "Temperature anomaly (°C)",
      data: stripes,
    },
  ],
});
