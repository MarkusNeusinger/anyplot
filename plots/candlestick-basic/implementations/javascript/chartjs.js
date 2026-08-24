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
const barBorderColors = [];
const barBorderWidths = [];

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
  const isBearish = close < open;

  labels.push(date.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
  opens.push(open);
  highs.push(high);
  lows.push(low);
  closes.push(close);
  barColors.push(isBearish ? t.palette[4] : t.palette[0]);
  // Redundant shape cue (VQ-04): bearish bodies get an ink outline so
  // direction doesn't rely on hue alone for colorblind viewers.
  barBorderColors.push(isBearish ? t.ink : "transparent");
  barBorderWidths.push(isBearish ? 1 : 0);

  price = close;
  date.setUTCDate(date.getUTCDate() + 1);
}

const priceMin = Math.min(...lows);
const priceMax = Math.max(...highs);
const pricePad = (priceMax - priceMin) * 0.15;

// --- Storytelling: highlight the single widest daily range -----------------
let widestIdx = 0;
let widestRange = 0;
for (let i = 0; i < sessionCount; i++) {
  const range = highs[i] - lows[i];
  if (range > widestRange) {
    widestRange = range;
    widestIdx = i;
  }
}

// --- 5-session moving average overlay ---------------------------------------
const maWindow = 5;
const movingAvg = closes.map((_, i) => {
  if (i < maWindow - 1) return null;
  let sum = 0;
  for (let j = i - maWindow + 1; j <= i; j++) sum += closes[j];
  return sum / maWindow;
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Annotation plugin -------------------------------------------------------
// Draws a muted vertical band + amber marker over the widest single-day range,
// using only core Chart.js plugin hooks (no external plugin package).
const widestRangePlugin = {
  id: "widestRangeHighlight",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const centerX = scales.x.getPixelForValue(widestIdx);
    const bandHalfWidth = 20;
    ctx.save();
    ctx.globalAlpha = 0.08;
    ctx.fillStyle = t.ink;
    ctx.fillRect(centerX - bandHalfWidth, chartArea.top, bandHalfWidth * 2, chartArea.bottom - chartArea.top);
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const centerX = scales.x.getPixelForValue(widestIdx);
    const topY = scales.y.getPixelForValue(highs[widestIdx]);
    const markerY = Math.max(topY - 14, chartArea.top + 14);

    let align = "center";
    let textX = centerX;
    if (centerX < chartArea.left + 80) {
      align = "left";
      textX = chartArea.left + 4;
    } else if (centerX > chartArea.right - 80) {
      align = "right";
      textX = chartArea.right - 4;
    }

    ctx.save();
    ctx.strokeStyle = t.amber;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(centerX, markerY + 6);
    ctx.lineTo(centerX, topY - 2);
    ctx.stroke();

    ctx.fillStyle = t.amber;
    ctx.beginPath();
    ctx.arc(centerX, markerY, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = t.ink;
    ctx.font = "13px sans-serif";
    ctx.textAlign = align;
    ctx.fillText(`Widest range: $${widestRange.toFixed(2)}`, textX, markerY - 10);
    ctx.restore();
  },
};

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
        borderColor: barBorderColors,
        borderWidth: barBorderWidths,
        barThickness: 18,
        grouped: false,
      },
      {
        type: "line",
        label: "5-session avg",
        data: movingAvg,
        borderColor: t.inkSoft,
        borderWidth: 2,
        borderDash: [6, 3],
        pointRadius: 0,
        spanGaps: false,
      },
    ],
  },
  plugins: [widestRangePlugin],
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
            { text: "5-session avg", fillStyle: t.inkSoft, strokeStyle: t.inkSoft, lineWidth: 0 },
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
