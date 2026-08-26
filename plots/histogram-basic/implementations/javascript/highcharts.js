// anyplot.ai
// histogram-basic: Basic Histogram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Retail transaction amounts ($), right-skewed: many small purchases, a
// gradually thinning tail of larger ones — a Gamma(shape=3, scale=40) draw
// via a sum of exponentials, generated with a fixed-seed LCG.
let seed = 42;
function random() {
  seed = (seed + 0x6d2b79f5) | 0;
  let z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
  return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
}
function exponential(rate) {
  return -Math.log(1 - random()) / rate;
}

const SAMPLE_SIZE = 400;
const GAMMA_SCALE = 40;
const transactionAmounts = [];
for (let i = 0; i < SAMPLE_SIZE; i++) {
  const gamma =
    exponential(1 / GAMMA_SCALE) +
    exponential(1 / GAMMA_SCALE) +
    exponential(1 / GAMMA_SCALE);
  transactionAmounts.push(gamma);
}

// --- Binning -----------------------------------------------------------------
const BIN_COUNT = 24;
const dataMin = Math.min(...transactionAmounts);
const dataMax = Math.max(...transactionAmounts);
const binWidth = (dataMax - dataMin) / BIN_COUNT;

const binCounts = new Array(BIN_COUNT).fill(0);
transactionAmounts.forEach((value) => {
  const idx = Math.min(
    BIN_COUNT - 1,
    Math.floor((value - dataMin) / binWidth)
  );
  binCounts[idx] += 1;
});

const histogramData = binCounts.map((count, idx) => ({
  x: dataMin + (idx + 0.5) * binWidth,
  y: count,
}));

// --- Chart -------------------------------------------------------------------
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
    text: "histogram-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "Transaction Amount ($)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return "$" + Math.round(this.value);
      },
    },
  },
  yAxis: {
    min: 0,
    title: {
      text: "Frequency",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: {
    headerFormat: "",
    pointFormatter() {
      const lo = this.x - binWidth / 2;
      const hi = this.x + binWidth / 2;
      return `$${lo.toFixed(0)}–$${hi.toFixed(0)}: <b>${this.y}</b>`;
    },
  },
  plotOptions: {
    series: { animation: false },
    column: {
      pointRange: binWidth,
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 1,
      borderColor: t.pageBg,
    },
  },
  series: [{ name: "Transactions", data: histogramData, color: t.palette[0] }],
});
