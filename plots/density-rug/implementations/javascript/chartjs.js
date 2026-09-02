// anyplot.ai
// density-rug: Density Plot with Rug Marks
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Support-ticket first-response times (minutes): a fast "auto-triaged" cohort
// and a slower "needs a human" cohort — a realistic bimodal shape.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}
const rand = lcg(42);
function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const responseTimes = [];
for (let i = 0; i < 110; i++) {
  responseTimes.push(Math.max(0.2, 2.6 + gaussian() * 0.55));
}
for (let i = 0; i < 70; i++) {
  responseTimes.push(Math.max(0.2, 6.3 + gaussian() * 1.15));
}

// --- Kernel density estimate (Gaussian kernel, Silverman bandwidth) --------
const n = responseTimes.length;
const mean = responseTimes.reduce((a, b) => a + b, 0) / n;
const variance =
  responseTimes.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);
const bandwidth = 1.06 * std * n ** (-1 / 5);

function gaussianKernel(u) {
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
}
function density(x) {
  const sum = responseTimes.reduce(
    (acc, xi) => acc + gaussianKernel((x - xi) / bandwidth),
    0,
  );
  return sum / (n * bandwidth);
}

const dataMin = Math.min(...responseTimes);
const dataMax = Math.max(...responseTimes);
const gridMin = Math.max(0, dataMin - 3 * bandwidth);
const gridMax = dataMax + 3 * bandwidth;
const gridSteps = 200;
const curve = Array.from({ length: gridSteps + 1 }, (_, i) => {
  const x = gridMin + ((gridMax - gridMin) * i) / gridSteps;
  return { x, y: density(x) };
});
const peakDensity = Math.max(...curve.map((p) => p.y));

// --- Color helpers -----------------------------------------------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const brand = t.palette[0];

// --- Mount --------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Rug marks plugin (core Chart.js plugin API — no external dependency) ---
const rugTickHeight = 22;
const rugPlugin = {
  id: "rugMarks",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const xScale = scales.x;
    ctx.save();
    ctx.strokeStyle = hexToRgba(brand, 0.4);
    ctx.lineWidth = 1.5;
    responseTimes.forEach((value) => {
      const xPixel = xScale.getPixelForValue(value);
      ctx.beginPath();
      ctx.moveTo(xPixel, chartArea.bottom);
      ctx.lineTo(xPixel, chartArea.bottom - rugTickHeight);
      ctx.stroke();
    });
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Density estimate",
        data: curve,
        parsing: false,
        borderColor: brand,
        backgroundColor: hexToRgba(brand, 0.2),
        borderWidth: 3,
        fill: "origin",
        tension: 0.3,
        pointRadius: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { bottom: 4 } },
    plugins: {
      title: {
        display: true,
        text: "density-rug · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: gridMin,
        max: gridMax,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "First Response Time (minutes)",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        beginAtZero: true,
        suggestedMax: peakDensity * 1.2,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        border: { display: false },
        title: {
          display: true,
          text: "Density",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
  plugins: [rugPlugin],
});
