// anyplot.ai
// histogram-kde: Histogram with KDE Overlay
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny LCG PRNG + Box-Muller — the browser has no seeded RNG.
function makeLcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (1103515245 * state + 12345) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
function randNormal() {
  let u1 = 0;
  while (u1 === 0) u1 = rand();
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Marketing analytics scenario: right-skewed customer session durations.
const sampleSize = 600;
const sessionDurations = [];
for (let i = 0; i < sampleSize; i++) {
  sessionDurations.push(Math.exp(2.85 + 0.5 * randNormal()));
}

// --- Histogram (density-scaled, not counts) ---------------------------------
const dataMin = Math.min(...sessionDurations);
const dataMax = Math.max(...sessionDurations);
const binCount = 28;
const binWidth = (dataMax - dataMin) / binCount;
const counts = new Array(binCount).fill(0);
sessionDurations.forEach((v) => {
  const idx = Math.min(binCount - 1, Math.floor((v - dataMin) / binWidth));
  counts[idx]++;
});
const histogramData = counts.map((count, i) => [
  dataMin + (i + 0.5) * binWidth,
  count / (sampleSize * binWidth),
]);

// --- Kernel density estimate (Gaussian kernel, Silverman's rule bandwidth) --
const mean = sessionDurations.reduce((a, b) => a + b, 0) / sampleSize;
const variance =
  sessionDurations.reduce((a, b) => a + (b - mean) ** 2, 0) / (sampleSize - 1);
const std = Math.sqrt(variance);
const sorted = [...sessionDurations].sort((a, b) => a - b);
function quantile(arr, q) {
  const pos = (arr.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return arr[base + 1] !== undefined
    ? arr[base] + rest * (arr[base + 1] - arr[base])
    : arr[base];
}
const iqr = quantile(sorted, 0.75) - quantile(sorted, 0.25);
const bandwidth =
  0.9 * Math.min(std, iqr / 1.34) * Math.pow(sampleSize, -0.2);

const gridPoints = 200;
const kdeMin = Math.max(0, dataMin - 3 * bandwidth);
const kdeMax = dataMax + 3 * bandwidth;
const kdeData = [];
for (let i = 0; i < gridPoints; i++) {
  const x = kdeMin + ((kdeMax - kdeMin) * i) / (gridPoints - 1);
  let sum = 0;
  for (let j = 0; j < sampleSize; j++) {
    const u = (x - sessionDurations[j]) / bandwidth;
    sum += Math.exp(-0.5 * u * u);
  }
  kdeData.push([x, sum / (sampleSize * bandwidth * Math.sqrt(2 * Math.PI))]);
}

// --- Chart -------------------------------------------------------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "histogram-kde · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "linear",
    title: {
      text: "Session Duration (minutes)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Density",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    lineColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    headerFormat: "",
    pointFormat: "{series.name}: <b>{point.y:.3f}</b>",
  },
  plotOptions: {
    series: { animation: false },
    column: { pointPadding: 0, groupPadding: 0, borderWidth: 0 },
  },
  series: [
    {
      name: "Histogram",
      type: "column",
      data: histogramData,
      pointRange: binWidth,
      color: hexToRgba(t.palette[0], 0.5),
    },
    {
      name: "KDE",
      type: "spline",
      data: kdeData,
      color: t.palette[1],
      lineWidth: 2.5,
      marker: { enabled: false },
    },
  ],
});
