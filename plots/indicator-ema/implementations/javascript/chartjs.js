// anyplot.ai
// indicator-ema: Exponential Moving Average (EMA) Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const periods = 120;
const shortPeriod = 12;
const longPeriod = 26;

const dates = [];
let cursor = new Date(2024, 0, 2);
while (dates.length < periods) {
  const day = cursor.getDay();
  if (day !== 0 && day !== 6) {
    dates.push(new Date(cursor));
  }
  cursor.setDate(cursor.getDate() + 1);
}
const labels = dates.map((d) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" }));

const close = [];
let price = 148;
let drift = 0.35;
for (let i = 0; i < periods; i++) {
  if (i % 18 === 0) drift = (rand() - 0.45) * 1.4;
  price += drift + (rand() - 0.5) * 3.2;
  price = Math.max(price, 40);
  close.push(price);
}

function ema(values, period) {
  const alpha = 2 / (period + 1);
  const out = [values[0]];
  for (let i = 1; i < values.length; i++) {
    out.push(values[i] * alpha + out[i - 1] * (1 - alpha));
  }
  return out;
}

const emaShort = ema(close, shortPeriod);
const emaLong = ema(close, longPeriod);

// Crossover markers on the short EMA line: bullish (golden cross) → brand
// green, bearish (death cross) → matte red — the finance color convention.
const crossPointRadius = new Array(periods).fill(0);
const crossPointColor = new Array(periods).fill("rgba(0,0,0,0)");
for (let i = 1; i < periods; i++) {
  const prevDiff = emaShort[i - 1] - emaLong[i - 1];
  const currDiff = emaShort[i] - emaLong[i];
  if (prevDiff <= 0 && currDiff > 0) {
    crossPointRadius[i] = 7;
    crossPointColor[i] = t.palette[0];
  } else if (prevDiff >= 0 && currDiff < 0) {
    crossPointRadius[i] = 7;
    crossPointColor[i] = "#AE3030";
  }
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "Close",
        data: close,
        borderColor: t.ink,
        backgroundColor: t.ink,
        borderWidth: 3,
        pointRadius: 0,
        tension: 0,
        order: 3,
      },
      {
        label: `EMA ${longPeriod}`,
        data: emaLong,
        borderColor: t.palette[2],
        backgroundColor: t.palette[2],
        borderWidth: 2.2,
        pointRadius: 0,
        tension: 0.1,
        order: 2,
      },
      {
        label: `EMA ${shortPeriod}`,
        data: emaShort,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 2.2,
        tension: 0.1,
        pointRadius: crossPointRadius,
        pointBackgroundColor: crossPointColor,
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        order: 1,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      title: {
        display: true,
        text: "indicator-ema · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24, usePointStyle: true, pointStyle: "line" },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, autoSkip: true, maxRotation: 0, maxTicksLimit: 10 },
        grid: { display: false },
        title: { display: true, text: "Trading Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `$${v.toFixed(0)}` },
        grid: { color: t.grid },
        title: { display: true, text: "Price (USD)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
