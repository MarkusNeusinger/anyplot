// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
// Package delivery times (minutes) — a right-skewed distribution where the
// cumulative view answers "what share of packages arrive within X minutes?"
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randomNormal(mean, stdDev) {
  const u1 = lcgRandom() || 1e-9;
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const sampleCount = 400;
const deliveryTimes = [];
for (let i = 0; i < sampleCount; i++) {
  const base = Math.exp(randomNormal(Math.log(30), 0.35));
  deliveryTimes.push(Math.max(5, base));
}

const binWidth = 5;
const maxTime = Math.max(...deliveryTimes);
const binCount = Math.ceil(maxTime / binWidth) + 1;
const binCounts = new Array(binCount).fill(0);
for (const value of deliveryTimes) {
  binCounts[Math.floor(value / binWidth)] += 1;
}

const binLabels = binCounts.map((_, i) => `${i * binWidth}–${(i + 1) * binWidth}`);
let running = 0;
const cumulativeProportion = binCounts.map((count) => {
  running += count;
  return running / sampleCount;
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: binLabels,
    datasets: [
      {
        label: "Cumulative proportion",
        data: cumulativeProportion,
        backgroundColor: t.palette[0],
        borderWidth: 0,
        barPercentage: 1.0,
        categoryPercentage: 1.0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "histogram-cumulative · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxRotation: 0, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Delivery Time (minutes)", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: 0,
        max: 1,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `${Math.round(value * 100)}%`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Cumulative Share of Deliveries", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
