// anyplot.ai
// indicator-ema: Exponential Moving Average (EMA) Indicator Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
// LCG PRNG (Numerical Recipes constants) — browser has no seeded RNG.
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const numPeriods = 120;
const dates = [];
const closePrices = [];

const startDate = Date.UTC(2024, 0, 2);
let price = 148;
// Piecewise drift so the price wanders through a downtrend, an uptrend, then
// a rollover — enough regime change to produce a handful of real EMA crosses.
for (let i = 0; i < numPeriods; i++) {
  dates.push(startDate + i * 86400000);
  let drift;
  if (i < 35) drift = -0.35;
  else if (i < 80) drift = 0.55;
  else drift = -0.25;
  price += drift + (nextRandom() - 0.5) * 3.2;
  price = Math.max(price, 20);
  closePrices.push(Math.round(price * 100) / 100);
}

function computeEma(values, period) {
  const k = 2 / (period + 1);
  const ema = new Array(values.length);
  ema[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    ema[i] = values[i] * k + ema[i - 1] * (1 - k);
  }
  return ema;
}

const shortPeriod = 12;
const longPeriod = 26;
const emaShort = computeEma(closePrices, shortPeriod);
const emaLong = computeEma(closePrices, longPeriod);

// Crossover points: golden cross (short over long, bullish) vs death cross
// (short under long, bearish) — the spec explicitly calls out highlighting
// these, so they carry real information rather than decorative annotation.
// Scan starts once both EMAs have warmed up past the long period — both
// series seed from the same first close, so an earlier start would flag
// that shared seed as a spurious "cross".
const goldenCrosses = [];
const deathCrosses = [];
for (let i = longPeriod; i < numPeriods; i++) {
  const prevDiff = emaShort[i - 1] - emaLong[i - 1];
  const diff = emaShort[i] - emaLong[i];
  if (prevDiff <= 0 && diff > 0) goldenCrosses.push([dates[i], emaShort[i]]);
  else if (prevDiff >= 0 && diff < 0)
    deathCrosses.push([dates[i], emaShort[i]]);
}

const closeSeries = closePrices.map((v, i) => [dates[i], v]);
const shortSeries = emaShort.map((v, i) => [
  dates[i],
  Math.round(v * 100) / 100,
]);
const longSeries = emaLong.map((v, i) => [dates[i], Math.round(v * 100) / 100]);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "indicator-ema · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Price (USD)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return "$" + this.value;
      },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    {
      name: "Close price",
      type: "line",
      data: closeSeries,
      color: t.palette[0],
      lineWidth: 3,
    },
    {
      name: `EMA ${shortPeriod}`,
      type: "line",
      data: shortSeries,
      color: t.palette[1],
      lineWidth: 2,
    },
    {
      name: `EMA ${longPeriod}`,
      type: "line",
      data: longSeries,
      color: t.palette[2],
      lineWidth: 2,
    },
    {
      name: "Golden cross",
      type: "scatter",
      data: goldenCrosses,
      color: t.palette[0],
      marker: {
        enabled: true,
        radius: 7,
        symbol: "triangle",
        lineWidth: 1,
        lineColor: t.ink,
      },
    },
    {
      name: "Death cross",
      type: "scatter",
      data: deathCrosses,
      color: "#AE3030",
      marker: {
        enabled: true,
        radius: 7,
        symbol: "triangle-down",
        lineWidth: 1,
        lineColor: t.ink,
      },
    },
  ],
});
