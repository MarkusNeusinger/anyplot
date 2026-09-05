// anyplot.ai
// histogram-stacked: Stacked Histogram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Fixed-seed LCG — the browser has no seeded Math.random
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal(mean, stdDev) {
  const u1 = lcgRandom() || 1e-9;
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const modes = ["Car", "Bus", "Train"];
const modeParams = {
  Car: { mean: 22, stdDev: 6, count: 220 },
  Bus: { mean: 34, stdDev: 8, count: 180 },
  Train: { mean: 28, stdDev: 5, count: 150 },
};

const commuteTimes = [];
modes.forEach((mode) => {
  const { mean, stdDev, count } = modeParams[mode];
  for (let i = 0; i < count; i++) {
    commuteTimes.push({ mode, minutes: Math.max(2, randNormal(mean, stdDev)) });
  }
});

// Shared bin boundaries applied to every group
const binWidth = 5;
const minValue = Math.floor(Math.min(...commuteTimes.map((d) => d.minutes)) / binWidth) * binWidth;
const maxValue = Math.ceil(Math.max(...commuteTimes.map((d) => d.minutes)) / binWidth) * binWidth;
const binCount = Math.round((maxValue - minValue) / binWidth);
const binLabels = Array.from(
  { length: binCount },
  (_, i) => `${minValue + i * binWidth}-${minValue + (i + 1) * binWidth}`,
);

const seriesData = {};
modes.forEach((mode) => {
  seriesData[mode] = new Array(binCount).fill(0);
});
commuteTimes.forEach(({ mode, minutes }) => {
  const binIndex = Math.min(Math.max(Math.floor((minutes - minValue) / binWidth), 0), binCount - 1);
  seriesData[mode][binIndex] += 1;
});

// --- Chart -------------------------------------------------------------
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
    text: "histogram-stacked · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: binLabels,
    title: { text: "Commute Time (minutes)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Number of Commuters", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false, stacking: "normal" },
    column: { borderWidth: 0, pointPadding: 0.05, groupPadding: 0 },
  },
  series: modes.map((mode) => ({ name: mode, data: seriesData[mode] })),
});
