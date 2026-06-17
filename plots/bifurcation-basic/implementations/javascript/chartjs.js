// anyplot.ai
// bifurcation-basic: Bifurcation Diagram for Dynamical Systems
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-17

const t = window.ANYPLOT_TOKENS;

// Convert Imprint hex color to rgba for alpha support
function hexAlpha(hex, a) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
}

// --- Data: Logistic map x(n+1) = r * x(n) * (1 - x(n)) ---
const R_MIN = 2.5, R_MAX = 4.0;
const N_R = 1000;     // r values sampled across [2.5, 4.0]
const N_SKIP = 200;   // transient iterations to discard
const N_PLOT = 100;   // steady-state iterations to record

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

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Bifurcation point annotations drawn as dashed vertical lines ---
// r=3.449 and r=3.544 are very close (~89 px apart), so their labels
// are staggered in y to prevent overlap.
const BIFURC = [
  { r: 3.0,   text: "r≈3.0 (period-2)",  dy: 14 },
  { r: 3.449, text: "r≈3.449 (period-4)", dy: 14 },
  { r: 3.544, text: "r≈3.544 (period-8)", dy: 34 },
];

const annotationPlugin = {
  id: "bifurcAnnot",
  afterDraw(chart) {
    const { ctx, chartArea: { top, bottom }, scales } = chart;
    ctx.save();

    BIFURC.forEach(({ r, text, dy }) => {
      const xPx = scales.x.getPixelForValue(r);

      // Dashed vertical reference line
      ctx.beginPath();
      ctx.setLineDash([7, 5]);
      ctx.strokeStyle = hexAlpha(t.ink, 0.28);
      ctx.lineWidth = 1.5;
      ctx.moveTo(xPx, top);
      ctx.lineTo(xPx, bottom);
      ctx.stroke();
      ctx.setLineDash([]);

      // Label inside chart area near y=1 (data is sparse there at these r values)
      ctx.fillStyle = t.inkSoft;
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(text, xPx, top + dy);
    });

    ctx.restore();
  },
};

// --- Chart ---
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [{
      label: "Logistic map",
      data: points,
      backgroundColor: hexAlpha(t.palette[0], 0.10),  // Imprint brand green, low alpha for density
      borderColor: "transparent",
      borderWidth: 0,
      pointRadius: 0.8,
      pointHoverRadius: 0,
    }],
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
        font: { size: 22, weight: "500" },
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
  plugins: [annotationPlugin],
});
