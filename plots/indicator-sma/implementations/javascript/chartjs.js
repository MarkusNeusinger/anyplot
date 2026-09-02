// anyplot.ai
// indicator-sma: Simple Moving Average (SMA) Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG random walk) ------------------------
function lcg(seed) {
  let state = seed;
  return function next() {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const rand = lcg(42);

const numDays = 320;
const dates = [];
const close = [];
let price = 148;
let cursor = new Date(2023, 0, 2);
while (dates.length < numDays) {
  const dow = cursor.getDay();
  if (dow !== 0 && dow !== 6) {
    dates.push(new Date(cursor));
    // regime shift: sustained uptrend, then a pullback — gives the SMAs
    // something to cross over
    const drift = dates.length < 170 ? 0.0009 : -0.0004;
    const shock = (rand() - 0.5) * 0.03;
    price *= 1 + drift + shock;
    close.push(price);
  }
  cursor.setDate(cursor.getDate() + 1);
}

function sma(values, period) {
  return values.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += values[j];
    return sum / period;
  });
}

const smaShort = sma(close, 20);
const smaMedium = sma(close, 50);
const smaLong = sma(close, 200);

// Golden-cross / death-cross emphasis: color each Close segment by whether
// price sits above (bullish, brand green) or below (bearish, semantic-red
// anchor) the medium SMA — a Chart.js `segment` feature that turns the
// crossover signal into the chart's visual focal point.
function crossState(i) {
  const s = smaMedium[i];
  if (s == null) return "above";
  return close[i] >= s ? "above" : "below";
}
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const bullish = t.palette[0]; // #009E73 brand green
const bearish = t.palette[4]; // #AE3030 matte-red semantic anchor
const bullishFill = hexToRgba(bullish, 0.14);
const bearishFill = hexToRgba(bearish, 0.1);

const labels = dates.map((d) =>
  d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" }),
);

// --- Title (fontsize scales down when the descriptive prefix pushes past the
// 67-char baseline) ----------------------------------------------------------
const title = "TechCorp Stock · indicator-sma · javascript · chartjs · anyplot.ai";
const titleFontSize = title.length > 67 ? Math.max(15, Math.round((22 * 67) / title.length)) : 22;

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
        borderColor: bullish,
        backgroundColor: bullishFill,
        borderWidth: 2,
        pointRadius: 0,
        tension: 0,
        // Fill the gap between Close and SMA 50 (dataset index 2) rather than
        // down to the axis bottom — a narrow, legible band that visualizes
        // the crossover spread instead of a heavy full-height area.
        fill: 2,
        segment: {
          borderColor: (ctx) => (crossState(ctx.p0DataIndex) === "below" ? bearish : bullish),
          backgroundColor: (ctx) => (crossState(ctx.p0DataIndex) === "below" ? bearishFill : bullishFill),
        },
      },
      {
        label: "SMA 20",
        data: smaShort,
        borderColor: t.palette[1],
        backgroundColor: t.palette[1],
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
        fill: false,
      },
      {
        label: "SMA 50",
        data: smaMedium,
        borderColor: t.palette[2],
        backgroundColor: t.palette[2],
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
        fill: false,
      },
      {
        label: "SMA 200",
        data: smaLong,
        borderColor: t.palette[3],
        backgroundColor: t.palette[3],
        borderWidth: 3,
        pointRadius: 0,
        tension: 0,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "nearest", intersect: false },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleFontSize, weight: "500" },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24, boxHeight: 3 },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 10, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Date", color: t.ink, font: { size: 18 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Price (USD)", color: t.ink, font: { size: 18 } },
      },
    },
  },
});
