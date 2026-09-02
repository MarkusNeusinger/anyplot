// anyplot.ai
// indicator-bollinger: Bollinger Bands Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: simulated BTC/USD daily close over 90 trading days --------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(1337);
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const N_DAYS = 90;
const WINDOW = 20;

const startDate = new Date(2024, 2, 1); // Mar 1 2024
const labels = Array.from({ length: N_DAYS }, (_, i) => {
  const d = new Date(startDate);
  d.setDate(d.getDate() + i);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
});

const close = [];
let price = 42000;
for (let i = 0; i < N_DAYS; i++) {
  price *= 1 + (0.0006 + 0.028 * randNormal());
  close.push(price);
}

// Rolling 20-day SMA + upper/lower bands (SMA ± 2 sample std dev)
const sma = [];
const upperBand = [];
const lowerBand = [];
for (let i = 0; i < N_DAYS; i++) {
  if (i < WINDOW - 1) {
    sma.push(null);
    upperBand.push(null);
    lowerBand.push(null);
    continue;
  }
  const slice = close.slice(i - WINDOW + 1, i + 1);
  const mean = slice.reduce((a, b) => a + b, 0) / WINDOW;
  const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / (WINDOW - 1);
  const std = Math.sqrt(variance);
  sma.push(mean);
  upperBand.push(mean + 2 * std);
  lowerBand.push(mean - 2 * std);
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const bandColor = t.palette[2]; // blue — volatility envelope
const smaColor = t.palette[1]; // lavender — middle band

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "Upper Band",
        data: upperBand,
        borderColor: bandColor,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.15,
      },
      {
        label: "Bollinger Band (±2σ)",
        data: lowerBand,
        borderColor: bandColor,
        backgroundColor: hexToRgba(bandColor, 0.15),
        borderWidth: 1.5,
        pointRadius: 0,
        fill: "-1",
        tension: 0.15,
      },
      {
        label: "SMA (20-day)",
        data: sma,
        borderColor: smaColor,
        backgroundColor: "transparent",
        borderWidth: 2.5,
        borderDash: [8, 4],
        pointRadius: 0,
        fill: false,
        tension: 0.15,
      },
      {
        label: "Close Price",
        data: close,
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        borderWidth: 3,
        pointRadius: 0,
        fill: false,
        tension: 0.15,
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
        text: "indicator-bollinger · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 12, bottom: 8 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 30,
          padding: 20,
          filter: (item) => item.text !== "Upper Band",
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Date", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 10, autoSkip: true },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: "Price (USD)", color: t.ink, font: { size: 18 } },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (v) => "$" + v.toLocaleString(),
        },
        grid: { color: t.grid },
      },
    },
  },
});
