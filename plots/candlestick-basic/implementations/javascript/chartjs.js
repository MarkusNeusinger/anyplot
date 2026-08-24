// anyplot.ai
// candlestick-basic: Basic Candlestick Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const sessionCount = 26;
const labels = [];
const opens = [];
const highs = [];
const lows = [];
const closes = [];
const barColors = [];

let price = 148;
const date = new Date(Date.UTC(2024, 0, 2));
for (let i = 0; i < sessionCount; i++) {
  while (date.getUTCDay() === 0 || date.getUTCDay() === 6) {
    date.setUTCDate(date.getUTCDate() + 1);
  }

  const open = price;
  const changePct = (rand() - 0.5) * 0.05;
  const close = open * (1 + changePct);
  const high = Math.max(open, close) * (1 + rand() * 0.012);
  const low = Math.min(open, close) * (1 - rand() * 0.012);

  labels.push(date.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
  opens.push(open);
  highs.push(high);
  lows.push(low);
  closes.push(close);
  barColors.push(close >= open ? t.palette[0] : t.palette[4]);

  price = close;
  date.setUTCDate(date.getUTCDate() + 1);
}

const priceMin = Math.min(...lows);
const priceMax = Math.max(...highs);
const pricePad = (priceMax - priceMin) * 0.15;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
// Core Chart.js has no dedicated candlestick type, so the candle is built from
// two overlaid floating-bar datasets on the same category axis: a thin "wick"
// (low -> high) and a wider "body" (open -> close), both centered on the same
// tick via grouped: false. This uses only core Chart.js bar-chart features.
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Wick",
        data: lows.map((low, i) => [low, highs[i]]),
        backgroundColor: barColors,
        borderWidth: 0,
        barThickness: 3,
        grouped: false,
      },
      {
        label: "Body",
        data: opens.map((open, i) => [open, closes[i]]),
        backgroundColor: barColors,
        borderWidth: 0,
        barThickness: 18,
        grouped: false,
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
        text: "candlestick-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          generateLabels: () => [
            { text: "Bullish (close ≥ open)", fillStyle: t.palette[0], strokeStyle: t.palette[0], lineWidth: 0 },
            { text: "Bearish (close < open)", fillStyle: t.palette[4], strokeStyle: t.palette[4], lineWidth: 0 },
          ],
        },
        onClick: () => {},
      },
      tooltip: {
        mode: "index",
        intersect: false,
        filter: (item) => item.dataset.label === "Body",
        callbacks: {
          label: (item) => {
            const i = item.dataIndex;
            return `O: $${opens[i].toFixed(2)}  H: $${highs[i].toFixed(2)}  L: $${lows[i].toFixed(2)}  C: $${closes[i].toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxRotation: 45,
          minRotation: 45,
          autoSkip: true,
          maxTicksLimit: 12,
        },
        grid: { display: false },
        title: { display: true, text: "Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: priceMin - pricePad,
        max: priceMax + pricePad,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => "$" + value.toFixed(0),
        },
        grid: { color: t.grid },
        title: { display: true, text: "Price (USD)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
