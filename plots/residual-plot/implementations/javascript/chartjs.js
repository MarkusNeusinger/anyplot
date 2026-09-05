// anyplot.ai
// residual-plot: Residual Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Simulated linear-regression diagnostics: fitted house-price predictions
// (in $1000s) vs. residuals, with mild heteroscedasticity (variance grows
// with fitted value) so the fan-out pattern is visible.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = 1 - lcg();
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const n = 220;
const fitted = [];
const residuals = [];
for (let i = 0; i < n; i++) {
  const value = 150 + lcg() * 450; // fitted price, $150k-$600k
  const noiseScale = 8 + (value - 150) * 0.05; // heteroscedastic spread
  fitted.push(value);
  residuals.push(gaussian() * noiseScale);
}

const mean = residuals.reduce((a, b) => a + b, 0) / n;
const variance = residuals.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const stdDev = Math.sqrt(variance);
const threshold = 2 * stdDev;

const normalPoints = [];
const outlierPoints = [];
for (let i = 0; i < n; i++) {
  const point = { x: fitted[i], y: residuals[i] };
  if (Math.abs(residuals[i]) > threshold) {
    outlierPoints.push(point);
  } else {
    normalPoints.push(point);
  }
}

const xMin = Math.min(...fitted);
const xMax = Math.max(...fitted);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "±2σ band",
        data: [
          { x: xMin, y: threshold },
          { x: xMax, y: threshold },
        ],
        showLine: true,
        borderColor: t.amber,
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: "+2",
        backgroundColor:
          t.pageBg === "#1A1A17" ? "rgba(240,239,232,0.06)" : "rgba(26,26,23,0.04)",
      },
      {
        label: "Zero reference",
        data: [
          { x: xMin, y: 0 },
          { x: xMax, y: 0 },
        ],
        showLine: true,
        borderColor: t.ink,
        borderWidth: 2,
        pointRadius: 0,
      },
      {
        label: "−2σ band",
        data: [
          { x: xMin, y: -threshold },
          { x: xMax, y: -threshold },
        ],
        showLine: true,
        borderColor: t.amber,
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
      },
      {
        label: "Residuals",
        data: normalPoints,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 6,
        pointHoverRadius: 7,
      },
      {
        label: "Outliers (>2σ)",
        data: outlierPoints,
        backgroundColor: t.palette[4],
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 7,
        pointStyle: "triangle",
        pointHoverRadius: 8,
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
        text: "residual-plot · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          filter: (item) => item.text !== "±2σ band" && item.text !== "−2σ band",
        },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        title: { display: true, text: "Fitted Value ($1,000s)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
      y: {
        title: { display: true, text: "Residual ($1,000s)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
    },
  },
});
