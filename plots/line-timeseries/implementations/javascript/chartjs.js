// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily closing price of a fictional tech stock across trading days of 2024.
// A tiny fixed-seed LCG stands in for a seeded RNG (the browser has none).
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

const dates = [];
const prices = [];
let price = 182;
const cursor = new Date(2024, 0, 2);
while (dates.length < 252) {
  const weekday = cursor.getDay();
  if (weekday !== 0 && weekday !== 6) {
    dates.push(new Date(cursor));
    const shock = (rand() - 0.5) * 6;
    const drift = 0.15;
    price = Math.max(20, price + drift + shock);
    prices.push(Math.round(price * 100) / 100);
  }
  cursor.setDate(cursor.getDate() + 1);
}

const dateLabels = dates.map((d) =>
  d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
);

// Smart tick selection: one tick per calendar month, label carries the year
// only at a year boundary (or the very first tick) — Chart.js has no bundled
// date adapter, so the "smart formatting" happens here rather than via a
// `type: 'time'` scale.
const monthTickIndices = new Set();
dates.forEach((d, i) => {
  if (i === 0 || d.getMonth() !== dates[i - 1].getMonth()) monthTickIndices.add(i);
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: dateLabels,
    datasets: [
      {
        label: "Closing Price ($)",
        data: prices,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill: false,
        tension: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "line-timeseries · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "category",
        afterBuildTicks: (axis) => {
          axis.ticks = axis.ticks.filter((tick) => monthTickIndices.has(tick.value));
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => {
            const d = dates[value];
            const isYearStart = value === 0 || d.getMonth() === 0;
            return isYearStart
              ? d.toLocaleDateString("en-US", { month: "short", year: "numeric" })
              : d.toLocaleDateString("en-US", { month: "short" });
          },
        },
        grid: { color: t.grid },
        title: { display: true, text: "Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `$${value}`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Closing Price ($)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
