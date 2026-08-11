// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function nextUniform() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function nextGaussian() {
  const u1 = Math.max(nextUniform(), 1e-9);
  const u2 = nextUniform();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Reference cuff (method2) vs. new oscillometric device (method1) — paired
// systolic blood pressure readings from the same subjects.
const N = 80;
const referenceCuff = [];
const newDevice = [];
for (let i = 0; i < N; i++) {
  const reference = 120 + nextGaussian() * 15;
  const bias = 3.2 + nextGaussian() * 5.5;
  referenceCuff.push(reference);
  newDevice.push(reference + bias);
}

const points = referenceCuff.map((reference, i) => ({
  x: (newDevice[i] + reference) / 2,
  y: newDevice[i] - reference,
}));

const diffs = points.map((p) => p.y);
const meanDiff = diffs.reduce((a, b) => a + b, 0) / diffs.length;
const variance = diffs.reduce((a, b) => a + (b - meanDiff) ** 2, 0) / (diffs.length - 1);
const sd = Math.sqrt(variance);
const upperLoA = meanDiff + 1.96 * sd;
const lowerLoA = meanDiff - 1.96 * sd;

const xValues = points.map((p) => p.x);
const xDataMin = Math.min(...xValues);
const xDataMax = Math.max(...xValues);
const xPad = (xDataMax - xDataMin) * 0.08;
const xMin = xDataMin - xPad;
const xMax = xDataMax + xPad;

// --- Colors -------------------------------------------------------------
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const pointFill = hexToRgba(t.palette[0], 0.55);

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Reference-line label plugin (native Chart.js plugin API, no external deps) --
const referenceLabelsPlugin = {
  id: "referenceLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const labelX = scales.x.getPixelForValue(xDataMin + (xDataMax - xDataMin) * 0.02);
    ctx.save();
    ctx.font = "600 15px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "bottom";
    ctx.fillStyle = t.ink;
    ctx.fillText(`Bias ${meanDiff.toFixed(2)} mmHg`, labelX, scales.y.getPixelForValue(meanDiff) - 6);
    ctx.fillStyle = t.inkSoft;
    ctx.fillText(`+1.96 SD  ${upperLoA.toFixed(2)} mmHg`, labelX, scales.y.getPixelForValue(upperLoA) - 6);
    ctx.fillText(`-1.96 SD  ${lowerLoA.toFixed(2)} mmHg`, labelX, scales.y.getPixelForValue(lowerLoA) - 6);
    ctx.restore();
  },
};

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        type: "scatter",
        label: "Paired readings",
        data: points,
        backgroundColor: pointFill,
        borderColor: t.pageBg,
        borderWidth: 1.5,
        pointRadius: 7,
        pointHoverRadius: 9,
      },
      {
        type: "line",
        label: "Mean bias",
        data: [
          { x: xMin, y: meanDiff },
          { x: xMax, y: meanDiff },
        ],
        borderColor: t.ink,
        borderWidth: 3,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        type: "line",
        label: "+1.96 SD limit",
        data: [
          { x: xMin, y: upperLoA },
          { x: xMax, y: upperLoA },
        ],
        borderColor: t.inkSoft,
        borderWidth: 2.5,
        borderDash: [10, 6],
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        type: "line",
        label: "-1.96 SD limit",
        data: [
          { x: xMin, y: lowerLoA },
          { x: xMax, y: lowerLoA },
        ],
        borderColor: t.inkSoft,
        borderWidth: 2.5,
        borderDash: [10, 6],
        pointRadius: 0,
        fill: false,
        tension: 0,
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
        text: "bland-altman-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 } },
      },
    },
    scales: {
      x: {
        min: xMin,
        max: xMax,
        title: {
          display: true,
          text: "Mean of Two Methods (mmHg)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: {
          display: true,
          text: "Difference: New Device − Reference (mmHg)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
  plugins: [referenceLabelsPlugin],
});
