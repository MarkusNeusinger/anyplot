// anyplot.ai
// precision-recall: Precision-Recall Curve
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic diagnostic-test scores for a rare condition -----------
function makeLcg(seed) {
  let state = seed;
  return function next() {
    state = (state * 9301 + 49297) % 233280;
    return state / 233280;
  };
}
const uniform = makeLcg(42);
function gaussian(mean, std) {
  const u1 = Math.max(uniform(), 1e-9);
  const u2 = uniform();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + std * z;
}

const N_PATIENTS = 400;
const PREVALENCE = 0.12;
const nPositive = Math.round(N_PATIENTS * PREVALENCE);
const nNegative = N_PATIENTS - nPositive;

const yTrue = [];
const yScores = [];
for (let i = 0; i < nPositive; i++) {
  yTrue.push(1);
  yScores.push(Math.min(1, Math.max(0, gaussian(0.72, 0.16))));
}
for (let i = 0; i < nNegative; i++) {
  yTrue.push(0);
  yScores.push(Math.min(1, Math.max(0, gaussian(0.28, 0.18))));
}

// --- Precision-recall curve (descending-score thresholds, sklearn-style) ---
const order = yScores.map((_, i) => i).sort((a, b) => yScores[b] - yScores[a]);

let truePositives = 0;
let falsePositives = 0;
const precisionPoints = [1];
const recallPoints = [0];
for (const i of order) {
  if (yTrue[i] === 1) truePositives += 1;
  else falsePositives += 1;
  precisionPoints.push(truePositives / (truePositives + falsePositives));
  recallPoints.push(truePositives / nPositive);
}

let averagePrecision = 0;
for (let i = 1; i < recallPoints.length; i++) {
  averagePrecision += (recallPoints[i] - recallPoints[i - 1]) * precisionPoints[i];
}

const prCurve = recallPoints.map((r, i) => ({ x: r, y: precisionPoints[i] }));
const baselinePrecision = nPositive / N_PATIENTS;

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: `Diagnostic test (AP = ${averagePrecision.toFixed(2)})`,
        data: prCurve,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        stepped: "after",
        borderWidth: 3.5,
        pointRadius: 0,
        fill: false,
      },
      {
        label: `Baseline (prevalence = ${baselinePrecision.toFixed(2)})`,
        data: [
          { x: 0, y: baselinePrecision },
          { x: 1, y: baselinePrecision },
        ],
        borderColor: t.inkSoft,
        borderDash: [8, 6],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
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
        text: "precision-recall · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 24 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 15 }, boxWidth: 24, boxHeight: 3 },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 1,
        title: { display: true, text: "Recall", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 0.2 },
        grid: { color: t.grid },
      },
      y: {
        min: 0,
        max: 1,
        title: { display: true, text: "Precision", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 0.2 },
        grid: { color: t.grid },
      },
    },
  },
});
