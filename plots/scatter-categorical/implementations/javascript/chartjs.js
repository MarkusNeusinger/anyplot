// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic, tiny fixed-seed LCG) -------------------
// Customer segments: monthly spend ($) vs. visit frequency (visits/month).
let seed = 20260905;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gauss(mean, spread) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * spread;
}
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const segments = [
  { name: "Budget", spend: 35, spendSpread: 12, visits: 2.2, visitSpread: 0.9, pointStyle: "circle" },
  { name: "Regular", spend: 85, spendSpread: 18, visits: 4.5, visitSpread: 1.2, pointStyle: "triangle" },
  { name: "Premium", spend: 160, spendSpread: 25, visits: 6.8, visitSpread: 1.4, pointStyle: "rect" },
  { name: "VIP", spend: 260, spendSpread: 30, visits: 9.5, visitSpread: 1.6, pointStyle: "rectRot" },
];

const nPerSegment = 35;
const datasets = segments.map((seg, i) => {
  const points = [];
  for (let p = 0; p < nPerSegment; p++) {
    points.push({
      x: Math.max(5, gauss(seg.spend, seg.spendSpread)),
      y: Math.max(0.2, gauss(seg.visits, seg.visitSpread)),
    });
  }
  return {
    label: seg.name,
    data: points,
    backgroundColor: hexToRgba(t.palette[i % t.palette.length], 0.8),
    borderColor: "#FFFFFF",
    borderWidth: 1,
    pointStyle: seg.pointStyle,
    pointRadius: 9,
    pointHoverRadius: 11,
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "scatter-categorical · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Monthly Spend ($)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: { display: true, text: "Visit Frequency (visits/month)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        beginAtZero: true,
      },
    },
  },
});
