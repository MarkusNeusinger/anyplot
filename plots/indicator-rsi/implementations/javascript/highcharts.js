// anyplot.ai
// indicator-rsi: RSI Technical Indicator Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic daily closes -> 14-period RSI (in-memory, deterministic) ---
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const numDays = 120;
const lookback = 14;
const totalDays = numDays + lookback;
// Alternate trending regimes so RSI actually breaches both the overbought
// and oversold thresholds, matching the spec's overbought/oversold use cases.
const regimeLength = 22;
const closes = [200];
for (let i = 1; i < totalDays; i += 1) {
  const regime = Math.floor(i / regimeLength) % 2;
  const drift = regime === 0 ? 1.1 : -1.1;
  const shock = (lcgRandom() - 0.5) * 4;
  const next = Math.max(20, closes[closes.length - 1] + drift + shock);
  closes.push(next);
}

function computeRsi(prices, period) {
  const values = [];
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = prices[i] - prices[i - 1];
    avgGain += Math.max(change, 0);
    avgLoss += Math.max(-change, 0);
  }
  avgGain /= period;
  avgLoss /= period;

  for (let i = period + 1; i < prices.length; i += 1) {
    const change = prices[i] - prices[i - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const rsi = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);
    values.push(Math.round(rsi * 100) / 100);
  }
  return values;
}

const rsiValues = computeRsi(closes, lookback);
const startDate = Date.UTC(2025, 2, 3);
const dayMs = 24 * 60 * 60 * 1000;
const rsiSeries = rsiValues.map((value, i) => [startDate + i * dayMs, value]);

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
    text: "indicator-rsi · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "14-period RSI",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: 0,
    max: 100,
    tickInterval: 10,
    title: { text: "RSI (0–100)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotBands: [
      { from: 70, to: 100, color: Highcharts.color(t.palette[4]).setOpacity(0.12).get() },
      { from: 0, to: 30, color: Highcharts.color(t.palette[2]).setOpacity(0.12).get() },
    ],
    plotLines: [
      { value: 70, color: t.palette[4], width: 1.5, dashStyle: "Dash",
        label: { text: "Overbought (70)", style: { color: t.inkSoft, fontSize: "12px" }, align: "right", x: -4 } },
      { value: 50, color: t.inkSoft, width: 1, dashStyle: "Dot",
        label: { text: "Centerline (50)", style: { color: t.inkSoft, fontSize: "12px" }, align: "right", x: -4 } },
      { value: 30, color: t.palette[2], width: 1.5, dashStyle: "Dash",
        label: { text: "Oversold (30)", style: { color: t.inkSoft, fontSize: "12px" }, align: "right", x: -4 } },
    ],
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    line: { lineWidth: 2.5, marker: { enabled: false } },
  },
  series: [
    {
      name: "RSI (14)",
      data: rsiSeries,
      color: t.palette[0],
      // Recolor the line itself while it's inside the oversold/overbought
      // zones, reinforcing the plotBands shading directly on the data.
      zoneAxis: "y",
      zones: [
        { value: 30, color: t.palette[2] },
        { value: 70, color: t.palette[0] },
        { color: t.palette[4] },
      ],
    },
  ],
});
