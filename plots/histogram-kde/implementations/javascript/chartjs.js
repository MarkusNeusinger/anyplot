// anyplot.ai
// histogram-kde: Histogram with KDE Overlay
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 79/100 | Created: 2026-08-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: simulated daily portfolio returns (%), deterministic LCG ---------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function rand() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal() {
  let u = 0;
  let v = 0;
  while (u === 0) u = rand();
  while (v === 0) v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const n = 600;
const returns = [];
for (let i = 0; i < n; i++) {
  // 92% calm-market days, 8% drawdown days (fat left tail)
  const isDrawdown = rand() < 0.08;
  returns.push(
    isDrawdown ? -3.2 + randNormal() * 2.0 : 0.15 + randNormal() * 1.1,
  );
}

// --- Histogram (density-scaled) ---------------------------------------------
const dataMin = Math.min(...returns);
const dataMax = Math.max(...returns);
const binCount = 24;
const binWidth = (dataMax - dataMin) / binCount;
const counts = new Array(binCount).fill(0);
returns.forEach((v) => {
  const idx = Math.min(binCount - 1, Math.floor((v - dataMin) / binWidth));
  counts[idx] += 1;
});
const histData = counts.map((c, i) => ({
  x: dataMin + (i + 0.5) * binWidth,
  y: c / (n * binWidth),
}));

// --- KDE overlay (Gaussian kernel, Silverman's rule bandwidth) --------------
const mean = returns.reduce((a, b) => a + b, 0) / n;
const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);
const bandwidth = 1.06 * std * Math.pow(n, -1 / 5);

function gaussianKernel(z) {
  return Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
}
function kde(x) {
  let sum = 0;
  for (let i = 0; i < n; i++)
    sum += gaussianKernel((x - returns[i]) / bandwidth);
  return sum / (n * bandwidth);
}

const gridPoints = 200;
const gridMin = dataMin - 3 * bandwidth;
const gridMax = dataMax + 3 * bandwidth;
const gridStep = (gridMax - gridMin) / (gridPoints - 1);
const kdeData = Array.from({ length: gridPoints }, (_, i) => {
  const x = gridMin + i * gridStep;
  return { x, y: kde(x) };
});

// --- Mount -------------------------------------------------------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  data: {
    datasets: [
      {
        type: "bar",
        label: "Histogram (density)",
        data: histData,
        backgroundColor: hexToRgba(t.palette[0], 0.5),
        borderColor: t.palette[0],
        borderWidth: 1,
        barPercentage: 1.0,
        categoryPercentage: 1.0,
        order: 1,
      },
      {
        type: "line",
        label: "KDE",
        data: kdeData,
        borderColor: t.palette[1],
        backgroundColor: "transparent",
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.3,
        order: 0,
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
        text: "histogram-kde · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 } },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: gridMin,
        max: gridMax,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Daily Return (%)",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Density",
          color: t.ink,
          font: { size: 16 },
        },
        beginAtZero: true,
      },
    },
  },
});
