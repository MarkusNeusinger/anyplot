// anyplot.ai
// indicator-sma: Simple Moving Average (SMA) Indicator Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Small LCG PRNG (the browser has no seeded RNG) feeding a Box-Muller
// transform, so the daily returns look like real market noise.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = 1 - lcgRandom();
  const u2 = lcgRandom();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const PERIODS = 300;
const dates = [];
let cursor = Date.UTC(2023, 0, 2);
while (dates.length < PERIODS) {
  const weekday = new Date(cursor).getUTCDay();
  if (weekday !== 0 && weekday !== 6) dates.push(cursor);
  cursor += 24 * 3600 * 1000;
}

const DRIFT = 0.0004;
const VOLATILITY = 0.012;
const closes = [];
let price = 148;
for (let i = 0; i < PERIODS; i++) {
  price *= 1 + DRIFT + VOLATILITY * gaussian();
  closes.push(Math.round(price * 100) / 100);
}

function sma(values, windowSize) {
  return values.map((_, i) => {
    if (i < windowSize - 1) return null;
    let sum = 0;
    for (let j = i - windowSize + 1; j <= i; j++) sum += values[j];
    return Math.round((sum / windowSize) * 100) / 100;
  });
}

const sma20 = sma(closes, 20);
const sma50 = sma(closes, 50);
const sma200 = sma(closes, 200);

const closeSeries = dates.map((d, i) => [d, closes[i]]);
const sma20Series = dates.map((d, i) => [d, sma20[i]]);
const sma50Series = dates.map((d, i) => [d, sma50[i]]);
const sma200Series = dates.map((d, i) => [d, sma200[i]]);

// --- Chart -----------------------------------------------------------------
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
    text: "indicator-sma · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Closing Price (USD)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { xDateFormat: "%b %e, %Y" },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    { name: "Close", data: closeSeries, lineWidth: 2, color: t.palette[0], zIndex: 4 },
    { name: "SMA 20", data: sma20Series, lineWidth: 1.5, color: t.palette[1], zIndex: 3 },
    { name: "SMA 50", data: sma50Series, lineWidth: 1.5, color: t.palette[2], zIndex: 2 },
    { name: "SMA 200", data: sma200Series, lineWidth: 1.5, color: t.palette[3], zIndex: 1 },
  ],
});
