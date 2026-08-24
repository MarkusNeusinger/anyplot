// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-24
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (1103515245 * state + 12345) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

const N = 70;
const products = [];
for (let i = 0; i < N; i++) {
  const price = 15 + rand() * 205; // $15 - $220
  const noise = (rand() - 0.5) * 4;
  const quality = Math.min(9.8, Math.max(2.0, 2.5 + (price / 220) * 4 + noise));
  const salesVolume = 10 + rand() * 90; // 10-100 units sold per month
  products.push({ price, quality, salesVolume });
}

const sizeValues = products.map((p) => p.salesVolume);
const sizeMin = Math.min(...sizeValues);
const sizeMax = Math.max(...sizeValues);
const R_MIN = 6;
const R_MAX = 42;

function bubbleRadius(size) {
  // area-proportional (not radius-proportional) to avoid overstating large values
  const frac = (size - sizeMin) / (sizeMax - sizeMin);
  const area = R_MIN * R_MIN + frac * (R_MAX * R_MAX - R_MIN * R_MIN);
  return Math.sqrt(area);
}

function hexToRgba(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const bubbleData = products.map((p) => ({
  x: p.price,
  y: p.quality,
  r: bubbleRadius(p.salesVolume),
}));

// --- Size legend plugin (static key explaining the bubble-area encoding) ---
const legendValues = [sizeMin, (sizeMin + sizeMax) / 2, sizeMax];
const sizeLegend = {
  id: "sizeLegend",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const cx = chartArea.left + R_MAX + 24;
    const spacing = 2 * R_MAX + 20;
    ctx.save();
    ctx.font = "13px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textAlign = "left";
    ctx.fillText("Monthly sales (units)", chartArea.left, chartArea.top + 14);
    legendValues.forEach((val, i) => {
      const r = bubbleRadius(val);
      const cy = chartArea.top + 36 + R_MAX + i * spacing;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = hexToRgba(t.palette[0], 0.35);
      ctx.fill();
      ctx.lineWidth = 1;
      ctx.strokeStyle = t.inkSoft;
      ctx.stroke();
      ctx.fillStyle = t.inkSoft;
      ctx.fillText(`${Math.round(val)}`, cx + R_MAX + 12, cy + 4);
    });
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bubble",
  data: {
    datasets: [
      {
        label: "Products",
        data: bubbleData,
        backgroundColor: hexToRgba(t.palette[0], 0.55),
        borderColor: t.pageBg,
        borderWidth: 1,
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
        text: "bubble-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Price ($)", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Quality Rating (1–10)", color: t.ink, font: { size: 16 } },
      },
    },
  },
  plugins: [sizeLegend],
});
