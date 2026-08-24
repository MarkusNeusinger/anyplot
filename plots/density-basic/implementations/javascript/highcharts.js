// anyplot.ai
// density-basic: Basic Density Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-24
const t = window.ANYPLOT_TOKENS;

// --- Data: reaction times (ms) in a cognitive test, right-skewed ----------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function exponential(mean) {
  return -Math.log(1 - rand()) * mean;
}

const sampleSize = 400;
const gammaShape = 4;
const componentMean = 45;
const baselineMs = 180;
const reactionTimes = Array.from({ length: sampleSize }, () => {
  let total = baselineMs;
  for (let i = 0; i < gammaShape; i++) total += exponential(componentMean);
  return total;
});

// --- Kernel density estimate (Gaussian kernel, Silverman bandwidth) -------
function mean(arr) {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}
function std(arr) {
  const m = mean(arr);
  const variance = arr.reduce((a, b) => a + (b - m) ** 2, 0) / (arr.length - 1);
  return Math.sqrt(variance);
}
function gaussianPdf(z) {
  return Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
}

const n = reactionTimes.length;
const bandwidth = 1.06 * std(reactionTimes) * n ** (-1 / 5);
const dataMin = Math.min(...reactionTimes);
const dataMax = Math.max(...reactionTimes);
const gridPoints = 200;
const gridMin = dataMin - 3 * bandwidth;
const gridMax = dataMax + 3 * bandwidth;
const step = (gridMax - gridMin) / (gridPoints - 1);

const densityCurve = [];
for (let i = 0; i < gridPoints; i++) {
  const x = gridMin + i * step;
  const density =
    reactionTimes.reduce((sum, xi) => sum + gaussianPdf((x - xi) / bandwidth), 0) /
    (n * bandwidth);
  densityCurve.push([x, density]);
}

const maxDensity = Math.max(...densityCurve.map((p) => p[1]));
const rugY = -maxDensity * 0.06;
const rugData = reactionTimes.map((v) => [v, rugY]);

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "areaspline",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "density-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Reaction Time (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: -maxDensity * 0.09,
    title: { text: "Probability Density", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    areaspline: {
      lineWidth: 3,
      fillOpacity: 0.3,
      marker: { enabled: false },
    },
    scatter: {
      marker: { radius: 3, symbol: "circle" },
      opacity: 0.5,
    },
  },
  series: [
    { type: "areaspline", name: "Density", data: densityCurve, color: t.palette[0] },
    { type: "scatter", name: "Observations", data: rugData, color: t.palette[0] },
  ],
});
