// anyplot.ai
// indicator-rsi: RSI Technical Indicator Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const LOOKBACK = 14;

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

const periods = 120;
const closes = [182.4];
for (let i = 1; i < periods; i++) {
  const momentumSwing = Math.sin(i / 8) * 1.3;
  const noise = (rand() - 0.5) * 2.4;
  closes.push(Math.max(5, closes[i - 1] + momentumSwing + noise));
}

// Wilder's smoothed RSI — the standard 14-period lookback.
function computeRSI(prices, lookback) {
  const rsi = new Array(prices.length).fill(null);
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= lookback; i++) {
    const change = prices[i] - prices[i - 1];
    avgGain += Math.max(change, 0);
    avgLoss += Math.max(-change, 0);
  }
  avgGain /= lookback;
  avgLoss /= lookback;
  rsi[lookback] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = lookback + 1; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    avgGain = (avgGain * (lookback - 1) + gain) / lookback;
    avgLoss = (avgLoss * (lookback - 1) + loss) / lookback;
    rsi[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return rsi;
}

const rsiByDay = computeRSI(closes, LOOKBACK);

const tradingDates = [];
const start = new Date("2024-01-02T00:00:00Z");
for (let i = 0; i < periods; i++) {
  const d = new Date(start);
  d.setUTCDate(d.getUTCDate() + i);
  tradingDates.push(d.toISOString().slice(0, 10));
}

// Only periods with a full 14-day lookback carry an RSI value.
const labels = tradingDates.slice(LOOKBACK);
const rsiSeries = rsiByDay.slice(LOOKBACK);
const constantLine = (value) => labels.map(() => value);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Zone shading plugin (core Chart.js plugin API, no external dependency) --
const rsiZonesPlugin = {
  id: "rsiZones",
  beforeDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const yScale = scales.y;
    const shadeZone = (from, to, color) => {
      const yTop = yScale.getPixelForValue(to);
      const yBottom = yScale.getPixelForValue(from);
      ctx.save();
      ctx.fillStyle = color;
      ctx.fillRect(chartArea.left, yTop, chartArea.right - chartArea.left, yBottom - yTop);
      ctx.restore();
    };
    shadeZone(70, 100, "rgba(174, 48, 48, 0.12)"); // overbought — matte red tint
    shadeZone(0, 30, "rgba(0, 158, 115, 0.10)"); // oversold — brand green tint
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: `RSI (${LOOKBACK})`,
        data: rsiSeries,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.15,
        fill: false,
      },
      {
        label: "Overbought (70)",
        data: constantLine(70),
        borderColor: "#AE3030",
        borderWidth: 1.5,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
      },
      {
        label: "Oversold (30)",
        data: constantLine(30),
        borderColor: t.palette[0],
        borderWidth: 1.5,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
      },
      {
        label: "Centerline (50)",
        data: constantLine(50),
        borderColor: t.inkSoft,
        borderWidth: 1,
        borderDash: [2, 4],
        pointRadius: 0,
        fill: false,
      },
    ],
  },
  plugins: [rsiZonesPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 16, bottom: 4, left: 4 } },
    plugins: {
      title: {
        display: true,
        text: "Daily RSI (14) · indicator-rsi · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          filter: (item) => item.text !== "Centerline (50)",
          usePointStyle: true,
          boxWidth: 10,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 13 }, maxTicksLimit: 10, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Trading Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: 0,
        max: 100,
        ticks: { color: t.inkSoft, font: { size: 13 }, stepSize: 10 },
        grid: { color: t.grid },
        title: { display: true, text: "RSI", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
