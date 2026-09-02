// anyplot.ai
// ohlc-bar: OHLC Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

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
const rand = lcg(7);

const sessionCount = 45;
const labels = [];
const opens = [];
const highs = [];
const lows = [];
const closes = [];
const barColors = [];

let price = 62; // crude oil futures, USD per barrel
const date = new Date(Date.UTC(2024, 2, 1));
for (let i = 0; i < sessionCount; i++) {
  while (date.getUTCDay() === 0 || date.getUTCDay() === 6) {
    date.setUTCDate(date.getUTCDate() + 1);
  }

  const open = price;
  const drift = (rand() - 0.48) * 1.6;
  const close = Math.max(open + drift, 1);
  const high = Math.max(open, close) + rand() * 0.9;
  const low = Math.min(open, close) - rand() * 0.9;
  const isUp = close >= open;

  labels.push(date.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
  opens.push(open);
  highs.push(high);
  lows.push(low);
  closes.push(close);
  barColors.push(isUp ? t.palette[0] : t.palette[4]);

  price = close;
  date.setUTCDate(date.getUTCDate() + 1);
}

const priceMin = Math.min(...lows);
const priceMax = Math.max(...highs);
const pricePad = (priceMax - priceMin) * 0.12;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Open/close tick plugin ---------------------------------------------------
// Draws the left (open) and right (close) horizontal ticks per bar directly on
// the canvas via a core Chart.js plugin hook — no external financial plugin.
const tickHalfWidth = 7;
const ohlcTicksPlugin = {
  id: "ohlcTicks",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.lineWidth = 3;
    for (let i = 0; i < sessionCount; i++) {
      const x = scales.x.getPixelForValue(i);
      const openY = scales.y.getPixelForValue(opens[i]);
      const closeY = scales.y.getPixelForValue(closes[i]);
      ctx.strokeStyle = barColors[i];

      ctx.beginPath();
      ctx.moveTo(x - tickHalfWidth, openY);
      ctx.lineTo(x, openY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(x, closeY);
      ctx.lineTo(x + tickHalfWidth, closeY);
      ctx.stroke();
    }
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
// Core Chart.js has no dedicated OHLC type, so the high-low range is a thin
// floating bar (one core "bar" dataset, data=[low, high]) and the open/close
// ticks are drawn with the plugin above. Only core Chart.js bar-chart and
// plugin-hook features are used — no chartjs-chart-financial or other package.
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Range",
        data: lows.map((low, i) => [low, highs[i]]),
        backgroundColor: barColors,
        borderWidth: 0,
        barThickness: 3,
      },
    ],
  },
  plugins: [ohlcTicksPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "ohlc-bar · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          generateLabels: () => [
            { text: "Up (close ≥ open)", fillStyle: t.palette[0], strokeStyle: t.palette[0], lineWidth: 0 },
            { text: "Down (close < open)", fillStyle: t.palette[4], strokeStyle: t.palette[4], lineWidth: 0 },
          ],
        },
        onClick: () => {},
      },
      tooltip: {
        mode: "index",
        intersect: false,
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
          maxTicksLimit: 14,
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
          callback: (value) => "$" + value.toFixed(2),
        },
        grid: { color: t.grid },
        title: { display: true, text: "Price (USD/barrel)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
