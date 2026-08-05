// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
// Patient response time (minutes) to a treatment, across escalating drug doses.
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const categories = ["Placebo", "Low Dose", "Standard Dose", "High Dose"];
const groupMeans = [42, 35, 24, 18];
const groupStd = [8, 7, 6, 5];
const perGroup = 45;
const jitterWidth = 0.22;

function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const datasets = categories.map((label, i) => ({
  label,
  data: Array.from({ length: perGroup }, () => ({
    x: i + (rand() - 0.5) * 2 * jitterWidth,
    y: Math.max(2, groupMeans[i] + groupStd[i] * gaussian()),
  })),
  backgroundColor: withAlpha(t.palette[i % t.palette.length], 0.65),
  pointRadius: 6,
  pointHoverRadius: 6,
  pointBorderWidth: 0,
}));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    plugins: {
      title: {
        display: true,
        text: "strip-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 24 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "linear",
        min: -0.6,
        max: categories.length - 1 + 0.6,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 1,
          callback: (value) => (Number.isInteger(value) && categories[value] !== undefined ? categories[value] : ""),
        },
        grid: { display: false },
        title: { display: true, text: "Treatment Group", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Response Time (minutes)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
