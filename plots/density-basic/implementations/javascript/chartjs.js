// anyplot.ai
// density-basic: Basic Density Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (mulberry32) ----------------------------------------
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

function randomNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Data: daily commute times (minutes), right-skewed ----------------------
const n = 400;
const commuteMinutes = [];
for (let i = 0; i < n; i++) {
  const minutes = Math.exp(3.1 + 0.35 * randomNormal());
  commuteMinutes.push(Math.max(4, minutes));
}

// --- Kernel density estimate (Gaussian kernel, Silverman bandwidth) --------
const mean = commuteMinutes.reduce((a, b) => a + b, 0) / n;
const variance =
  commuteMinutes.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);
const bandwidth = 1.06 * std * Math.pow(n, -1 / 5);

const dataMin = Math.min(...commuteMinutes);
const dataMax = Math.max(...commuteMinutes);
const pad = (dataMax - dataMin) * 0.15;
const gridStart = Math.max(0, Math.floor((dataMin - pad) / 5) * 5);
const gridEnd = Math.ceil((dataMax + pad) / 5) * 5;
const gridSize = 200;

function gaussianKernel(u) {
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
}

const densityPoints = [];
for (let i = 0; i <= gridSize; i++) {
  const x = gridStart + ((gridEnd - gridStart) * i) / gridSize;
  let sum = 0;
  for (let j = 0; j < n; j++) {
    sum += gaussianKernel((x - commuteMinutes[j]) / bandwidth);
  }
  densityPoints.push({ x, y: sum / (n * bandwidth) });
}

const maxDensity = Math.max(...densityPoints.map((p) => p.y));

// --- Rug plot: individual observations along the baseline -------------------
const rugY = -0.07 * maxDensity;
const rugPoints = commuteMinutes.map((minutes) => ({ x: minutes, y: rugY }));

// --- Fill color (Imprint brand green at low alpha) --------------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  data: {
    datasets: [
      {
        type: "line",
        label: "Density estimate",
        data: densityPoints,
        borderColor: t.palette[0],
        backgroundColor: hexToRgba(t.palette[0], 0.25),
        borderWidth: 3.5,
        pointRadius: 0,
        tension: 0.35,
        fill: "origin",
      },
      {
        type: "scatter",
        label: "Observations",
        data: rugPoints,
        pointStyle: "line",
        rotation: 90,
        radius: 9,
        borderColor: hexToRgba(t.palette[0], 0.45),
        borderWidth: 1.5,
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
        text: "density-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "linear",
        min: gridStart,
        max: gridEnd,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Commute Time (minutes)",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        min: rugY * 1.6,
        max: maxDensity * 1.15,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Density",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
