// anyplot.ai
// indicator-macd: MACD Technical Indicator Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const random = lcg(42);

const periods = 150;
const startDate = Date.UTC(2025, 5, 1);
const dayMs = 24 * 60 * 60 * 1000;

// Simulated daily closing price: cyclical drift + noise, deterministic
const closingPrices = [];
let price = 150;
for (let i = 0; i < periods; i++) {
  const drift = 0.15 * Math.sin(i / 18);
  const noise = (random() - 0.5) * 2.2;
  price += drift + noise;
  closingPrices.push(price);
}

// EMA seeded with the SMA of the first `period` values, standard MACD practice
function ema(values, period) {
  const k = 2 / (period + 1);
  const out = new Array(values.length).fill(null);
  let sum = 0;
  for (let i = 0; i < period; i++) sum += values[i];
  let prev = sum / period;
  out[period - 1] = prev;
  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    out[i] = prev;
  }
  return out;
}

const ema12 = ema(closingPrices, 12);
const ema26 = ema(closingPrices, 26);

// MACD line starts once the slower 26-day EMA is defined
const macdValues = [];
for (let i = 25; i < periods; i++) {
  macdValues.push(ema12[i] - ema26[i]);
}
const signalValues = ema(macdValues, 9);

const macdSeries = [];
const signalSeries = [];
const histogramSeries = [];
for (let j = 0; j < macdValues.length; j++) {
  const timestamp = startDate + (25 + j) * dayMs;
  macdSeries.push([timestamp, macdValues[j]]);
  if (signalValues[j] !== null) {
    signalSeries.push([timestamp, signalValues[j]]);
    histogramSeries.push([timestamp, macdValues[j] - signalValues[j]]);
  }
}

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "indicator-macd · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "12/26/9 EMA parameters",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "MACD Value",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      { value: 0, color: t.inkSoft, width: 1.5, dashStyle: "Dash", zIndex: 3 },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    column: { borderWidth: 0, pointPadding: 0.05, groupPadding: 0 },
    line: { lineWidth: 2.5, marker: { enabled: false } },
  },
  series: [
    {
      type: "column",
      name: "Histogram",
      data: histogramSeries,
      color: t.palette[0],
      negativeColor: t.palette[4],
    },
    {
      type: "line",
      name: "MACD Line",
      data: macdSeries,
      color: t.palette[2],
    },
    {
      type: "line",
      name: "Signal Line",
      data: signalSeries,
      color: t.palette[3],
    },
  ],
});
