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

// Best-value product (highest quality per dollar) drives the storytelling
// highlight below — a genuine insight beyond the raw x/y/size encoding.
let bestValueIndex = 0;
let bestValueScore = -Infinity;
products.forEach((p, i) => {
  const score = p.quality / p.price;
  if (score > bestValueScore) {
    bestValueScore = score;
    bestValueIndex = i;
  }
});

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
      ctx.font = "bold 15px sans-serif";
      ctx.fillStyle = t.inkSoft;
      ctx.fillText(`${Math.round(val)}`, cx + R_MAX + 12, cy + 5);
    });
    ctx.restore();
  },
};

// --- Standout annotation plugin (points at the best-value product) --------
const standoutAnnotation = {
  id: "standoutAnnotation",
  afterDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const p = products[bestValueIndex];
    const px = scales.x.getPixelForValue(p.price);
    const py = scales.y.getPixelForValue(p.quality);
    // Point below-right when near the top-left legend, otherwise above-right.
    const nearLegend = px < chartArea.left + 160 && py < chartArea.top + 140;
    const labelX = px + 20;
    const labelY = nearLegend ? py + 34 : py - 30;
    ctx.save();
    ctx.strokeStyle = t.ink;
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(labelX, labelY);
    ctx.stroke();
    ctx.font = "bold 14px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "left";
    ctx.fillText("Best value", labelX + 4, labelY + (nearLegend ? 4 : -4));
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
        // Scriptable options single out the best-value bubble (full opacity,
        // brand-green ring) while the rest stay at the spec-range overlap alpha.
        backgroundColor: (ctx) =>
          hexToRgba(t.palette[0], ctx.dataIndex === bestValueIndex ? 0.9 : 0.55),
        borderColor: (ctx) => (ctx.dataIndex === bestValueIndex ? t.palette[0] : t.pageBg),
        borderWidth: (ctx) => (ctx.dataIndex === bestValueIndex ? 2.5 : 1),
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
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const p = products[ctx.dataIndex];
            return `Price $${p.price.toFixed(0)} · Quality ${p.quality.toFixed(1)} · Sales ${Math.round(p.salesVolume)} units`;
          },
        },
      },
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
  plugins: [sizeLegend, standoutAnnotation],
});
