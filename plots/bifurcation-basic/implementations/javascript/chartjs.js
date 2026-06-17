// anyplot.ai
// bifurcation-basic: Bifurcation Diagram for Dynamical Systems
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-17

const t = window.ANYPLOT_TOKENS;
const rgba = (hex, a) => { const [r,g,b] = [1,3,5].map(o=>parseInt(hex.slice(o,o+2),16)); return `rgba(${r},${g},${b},${a})`; };

// --- Data: Logistic map x(n+1) = r * x(n) * (1 - x(n)) ---
const R_MIN = 2.5, R_MAX = 4.0;
const N_R = 1000;
const N_SKIP = 200;
const N_PLOT = 100;

const points = [];
for (let i = 0; i <= N_R; i++) {
  const r = R_MIN + (R_MAX - R_MIN) * i / N_R;
  let x = 0.5;
  for (let j = 0; j < N_SKIP; j++) x = r * x * (1 - x);
  for (let j = 0; j < N_PLOT; j++) {
    x = r * x * (1 - x);
    points.push({ x: r, y: x });
  }
}

// --- Bifurcation points: dashed vertical lines via Chart.js line datasets ---
// r=3.449 and r=3.544 are very close (~89 px apart); labels staggered in dy.
const BIFURC = [
  { r: 3.0,   text: "r≈3.0 (period-2)",  dy: 14 },
  { r: 3.449, text: "r≈3.449 (period-4)", dy: 14 },
  { r: 3.544, text: "r≈3.544 (period-8)", dy: 34 },
];

const refColor = rgba(t.ink, 0.28);
const refDatasets = BIFURC.map(({ r }) => ({
  type: "line",
  data: [{ x: r, y: 0 }, { x: r, y: 1 }],
  borderColor: refColor,
  borderWidth: 1.5,
  borderDash: [7, 5],
  pointRadius: 0,
  fill: false,
  tension: 0,
}));

// Plugin for annotation text labels only (lines handled by datasets above)
const labelPlugin = {
  id: "bifurcLabels",
  afterDraw({ ctx, chartArea: { top }, scales }) {
    ctx.save();
    ctx.fillStyle = t.inkSoft;
    ctx.font = "14px system-ui, sans-serif";
    ctx.textAlign = "center";
    BIFURC.forEach(({ r, text, dy }) => ctx.fillText(text, scales.x.getPixelForValue(r), top + dy));
    ctx.restore();
  },
};

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Per-theme alpha: slightly higher in light for better chaos-region visibility
const dotAlpha = window.ANYPLOT_THEME === "light" ? 0.13 : 0.10;

// --- Chart ---
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      ...refDatasets,
      {
        label: "Logistic map",
        data: points,
        backgroundColor: rgba(t.palette[0], dotAlpha),
        borderColor: "transparent",
        borderWidth: 0,
        pointRadius: 0.8,
        pointHoverRadius: 0,
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
        text: "bifurcation-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500", family: "system-ui, sans-serif" },
        padding: { top: 12, bottom: 18 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: R_MIN,
        max: R_MAX,
        border: { display: false },
        title: {
          display: true,
          text: "Growth Rate Parameter (r)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        type: "linear",
        min: 0,
        max: 1,
        border: { display: false },
        title: {
          display: true,
          text: "Population Value (x)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
  plugins: [labelPlugin],
});
