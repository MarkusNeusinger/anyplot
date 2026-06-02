// anyplot.ai
// area-basic: Basic Area Chart
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: daily website visitors over a 30-day month -----------------------
// Deterministic seeded LCG so the silhouette is identical across renders.
const SEED = 42;
let _s = SEED;
const rand = () => {
  _s = (_s * 1664525 + 1013904223) >>> 0;
  return _s / 0x100000000;
};

const days = 30;
const labels = [];
const visitors = [];
const baseline = 2200;
const growth = 38;
const weekendLift = 520;
for (let i = 0; i < days; i++) {
  const date = new Date(2025, 8, i + 1);
  labels.push(date.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
  const dow = date.getDay();
  const weekend = dow === 0 || dow === 6 ? weekendLift : 0;
  const noise = (rand() - 0.5) * 600;
  visitors.push(Math.round(baseline + growth * i + weekend + noise));
}

// --- Imprint brand-green fill, vertical gradient for depth ------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const BRAND = t.palette[0];
// CanvasGradient: opaque brand green at the line, fading to transparent at the axis.
const areaGradient = (ctx) => {
  const { chartArea } = ctx.chart;
  if (!chartArea) return hexToRgba(BRAND, 0.35);
  const g = ctx.chart.ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  g.addColorStop(0, hexToRgba(BRAND, 0.7));
  g.addColorStop(1, hexToRgba(BRAND, 0.05));
  return g;
};

// --- Peak annotation: highlight Sep 28 with a leader line + label -----------
const peakIdx = visitors.indexOf(Math.max(...visitors));
const peakLabel = `Peak: ${visitors[peakIdx].toLocaleString("en-US")} on ${labels[peakIdx]}`;
const peakAnnotation = {
  id: "peakAnnotation",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const x = scales.x.getPixelForValue(peakIdx);
    const y = scales.y.getPixelForValue(visitors[peakIdx]);
    const leaderEnd = y - 70;
    ctx.save();
    // Leader line
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(x, y - 6);
    ctx.lineTo(x, leaderEnd);
    ctx.stroke();
    ctx.setLineDash([]);
    // Peak dot
    ctx.fillStyle = BRAND;
    ctx.beginPath();
    ctx.arc(x, y, 5.5, 0, Math.PI * 2);
    ctx.fill();
    // Label
    ctx.font = "500 16px system-ui, -apple-system, sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textBaseline = "bottom";
    const textWidth = ctx.measureText(peakLabel).width;
    const padX = 10, padY = 6;
    const boxLeft = Math.min(x - textWidth / 2, scales.x.right - textWidth - padX);
    const labelX = Math.max(boxLeft, scales.x.left + padX);
    // Subtle pill background for legibility over the gradient
    ctx.fillStyle = t.elevatedBg;
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    const boxY = leaderEnd - 24;
    ctx.beginPath();
    ctx.rect(labelX - padX / 2, boxY, textWidth + padX, 24);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = t.ink;
    ctx.textBaseline = "middle";
    ctx.fillText(peakLabel, labelX, boxY + 12);
    ctx.restore();
  },
};

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "Daily visitors",
        data: visitors,
        borderColor: BRAND,
        backgroundColor: areaGradient,
        fill: { target: "origin", above: areaGradient },
        borderWidth: 3.5,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: BRAND,
        pointHoverBorderColor: t.pageBg,
        pointHoverBorderWidth: 2,
        tension: 0.3,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 24, right: 32, bottom: 12, left: 12 } },
    plugins: {
      title: {
        display: true,
        text: "area-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24, weight: "500" },
        padding: { top: 8, bottom: 28 },
      },
      legend: { display: false },
      tooltip: {
        backgroundColor: t.elevatedBg,
        titleColor: t.ink,
        bodyColor: t.inkSoft,
        borderColor: t.grid,
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 16 },
        bodyFont: { size: 14 },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Date (September 2025)",
          color: t.ink,
          font: { size: 20 },
          padding: { top: 14 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 16 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 10,
        },
        grid: { display: false },
        border: { color: t.grid },
      },
      y: {
        title: {
          display: true,
          text: "Visitors per day",
          color: t.ink,
          font: { size: 20 },
          padding: { bottom: 14 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 16 },
          padding: 8,
          callback: (v) => v.toLocaleString("en-US"),
        },
        grid: { color: t.grid, drawTicks: false },
        border: { display: false },
        beginAtZero: true,
        suggestedMax: Math.max(...visitors) * 1.1,
      },
    },
    interaction: { mode: "index", intersect: false },
  },
  plugins: [peakAnnotation],
});
