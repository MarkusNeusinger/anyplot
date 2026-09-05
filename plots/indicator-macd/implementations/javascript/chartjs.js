// anyplot.ai
// indicator-macd: MACD Technical Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
//# anyplot-orientation: landscape
// anyplot.ai
// indicator-macd: MACD Technical Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Small LCG for reproducible pseudo-randomness (Math.random() is not seeded)
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

function ema(values, period) {
  const k = 2 / (period + 1);
  const result = [];
  let prev = values[0];
  values.forEach((value, i) => {
    prev = i === 0 ? value : value * k + prev * (1 - k);
    result.push(prev);
  });
  return result;
}

const periods = 120;
const startDate = new Date("2024-03-01T00:00:00Z");
const dates = [];
const closes = [];
let price = 182;
for (let i = 0; i < periods; i++) {
  const d = new Date(startDate);
  d.setUTCDate(d.getUTCDate() + i);
  dates.push(`${d.getUTCMonth() + 1}/${d.getUTCDate()}`);
  price += (nextRandom() - 0.47) * 3.2;
  closes.push(price);
}

const emaFast = ema(closes, 12);
const emaSlow = ema(closes, 26);
const macdLine = emaFast.map((v, i) => v - emaSlow[i]);
const signalLine = ema(macdLine, 9);
const histogram = macdLine.map((v, i) => v - signalLine[i]);
const zeroLine = dates.map(() => 0);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
const bullColor = t.palette[0]; // #009E73 brand green — positive histogram / gain
const bearColor = t.palette[4]; // #AE3030 matte red — negative histogram / loss (semantic anchor)
const macdColor = t.palette[2]; // #4467A3 blue — MACD line
const signalColor = t.palette[3]; // #BD8233 ochre — signal line

new Chart(canvas, {
  type: "bar",
  data: {
    labels: dates,
    datasets: [
      {
        type: "bar",
        label: "Histogram",
        data: histogram,
        backgroundColor: histogram.map((v) => (v >= 0 ? bullColor : bearColor)),
        borderWidth: 0,
        barPercentage: 1.0,
        categoryPercentage: 0.9,
      },
      {
        type: "line",
        label: "Zero line",
        data: zeroLine,
        borderColor: t.grid,
        borderWidth: 1,
        borderDash: [6, 4],
        pointRadius: 0,
        pointHoverRadius: 0,
      },
      {
        type: "line",
        label: "MACD (12, 26)",
        data: macdLine,
        borderColor: macdColor,
        backgroundColor: macdColor,
        borderWidth: 3,
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0.15,
      },
      {
        type: "line",
        label: "Signal (9)",
        data: signalLine,
        borderColor: signalColor,
        backgroundColor: signalColor,
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0.15,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      title: {
        display: true,
        text: "indicator-macd · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 14 },
      },
      subtitle: {
        display: true,
        text: "12-day / 26-day EMA convergence-divergence, 9-day signal EMA",
        color: t.inkSoft,
        font: { size: 13, style: "italic" },
        padding: { bottom: 14 },
      },
      legend: {
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 14 },
          boxWidth: 24,
          usePointStyle: true,
          filter: (item) => item.text !== "Zero line",
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 12, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Trading Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "MACD Value", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
