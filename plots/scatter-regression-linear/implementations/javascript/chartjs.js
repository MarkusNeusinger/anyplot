// anyplot.ai
// scatter-regression-linear: Scatter Plot with Linear Regression
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 84/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
function randNormal(rand) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const rand = lcg(42);
const n = 70;
const trueSlope = 1.8;
const trueIntercept = 18;
const noiseSd = 14;

const adSpend = [];
const salesRevenue = [];
for (let i = 0; i < n; i++) {
  const x = 5 + rand() * 45; // $5k-$50k monthly ad spend
  const y = trueSlope * x + trueIntercept + randNormal(rand) * noiseSd;
  adSpend.push(x);
  salesRevenue.push(y);
}

// --- Least-squares fit + 95% confidence band --------------------------------
const xMean = adSpend.reduce((a, b) => a + b, 0) / n;
const yMean = salesRevenue.reduce((a, b) => a + b, 0) / n;
let sXY = 0;
let sXX = 0;
for (let i = 0; i < n; i++) {
  sXY += (adSpend[i] - xMean) * (salesRevenue[i] - yMean);
  sXX += (adSpend[i] - xMean) ** 2;
}
const slope = sXY / sXX;
const intercept = yMean - slope * xMean;

let ssRes = 0;
let ssTot = 0;
for (let i = 0; i < n; i++) {
  const yHat = slope * adSpend[i] + intercept;
  ssRes += (salesRevenue[i] - yHat) ** 2;
  ssTot += (salesRevenue[i] - yMean) ** 2;
}
const rSquared = 1 - ssRes / ssTot;
const seEstimate = Math.sqrt(ssRes / (n - 2));
const tCritical = 1.995; // t(0.975, df=68) — 95% CI

const xMin = Math.min(...adSpend);
const xMax = Math.max(...adSpend);
const steps = 40;
const regressionPoints = [];
const ciUpperPoints = [];
const ciLowerPoints = [];
for (let i = 0; i <= steps; i++) {
  const x0 = xMin + ((xMax - xMin) * i) / steps;
  const yHat = slope * x0 + intercept;
  const sePred = seEstimate * Math.sqrt(1 / n + (x0 - xMean) ** 2 / sXX);
  const margin = tCritical * sePred;
  regressionPoints.push({ x: x0, y: yHat });
  ciUpperPoints.push({ x: x0, y: yHat + margin });
  ciLowerPoints.push({ x: x0, y: yHat - margin });
}

const scatterPoints = adSpend.map((x, i) => ({ x, y: salesRevenue[i] }));

// --- Colors (Imprint palette) -----------------------------------------------
function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const pointColor = withAlpha(t.palette[0], 0.65);
const lineColor = t.palette[2];
const mutedInk = t.theme === "light" ? "#6B6A63" : "#A8A79F"; // muted anchor (confidence-band fill)
const bandColor = withAlpha(mutedInk, 0.18);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "",
        type: "line",
        data: ciUpperPoints,
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: "95% Confidence Interval",
        type: "line",
        data: ciLowerPoints,
        borderWidth: 0,
        pointRadius: 0,
        fill: "-1",
        backgroundColor: bandColor,
        tension: 0,
      },
      {
        label: "Linear regression",
        type: "line",
        data: regressionPoints,
        borderColor: lineColor,
        borderWidth: 3.5,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: "Observations",
        data: scatterPoints,
        backgroundColor: pointColor,
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 7,
        pointHoverRadius: 7,
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
        text: "scatter-regression-linear · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 6 },
      },
      subtitle: {
        display: true,
        text: [
          `R² = ${rSquared.toFixed(3)}  ·  y = ${slope.toFixed(2)}x + ${intercept.toFixed(1)}`,
        ],
        color: t.inkSoft,
        font: { size: 16 },
        padding: { bottom: 16 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => item.text !== "",
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Monthly Ad Spend ($1,000s)", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Monthly Sales Revenue ($1,000s)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
