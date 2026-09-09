// anyplot.ai
// volcano-basic: Volcano Plot for Statistical Significance
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
const INK_MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic LCG — proteomics case study) -----------
// Differential protein abundance, tumor vs. healthy tissue, mass-spec proteomics.
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal() {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const PVAL_THRESHOLD = 1.3; // -log10(0.05)
const FC_THRESHOLD = 1; // log2(2)

const nonSigPoints = [];
const downPoints = [];
const upPoints = [];

const nProteins = 1400;
for (let i = 0; i < nProteins; i++) {
  const log2FoldChange = randNormal() * 1.6;
  const signalBoost = Math.abs(log2FoldChange) / 2.4;
  const rawPValue = Math.exp(-rand() * 7 - signalBoost * 6);
  const negLog10Pvalue = Math.min(-Math.log10(Math.max(rawPValue, 1e-30)), 26);

  const point = { x: log2FoldChange, y: negLog10Pvalue };
  const isSignificant =
    negLog10Pvalue > PVAL_THRESHOLD && Math.abs(log2FoldChange) > FC_THRESHOLD;
  if (!isSignificant) {
    nonSigPoints.push(point);
  } else if (log2FoldChange > 0) {
    upPoints.push(point);
  } else {
    downPoints.push(point);
  }
}

const allY = [...nonSigPoints, ...downPoints, ...upPoints].map((p) => p.y);
const allX = [...nonSigPoints, ...downPoints, ...upPoints].map((p) => p.x);
const xLimit = Math.ceil(Math.max(...allX.map(Math.abs)) * 1.08 * 2) / 2;
const yLimit = Math.ceil(Math.max(...allY) * 1.08);

const horizontalThreshold = [
  { x: -xLimit, y: PVAL_THRESHOLD },
  { x: xLimit, y: PVAL_THRESHOLD },
];
const verticalThresholdDown = [
  { x: -FC_THRESHOLD, y: 0 },
  { x: -FC_THRESHOLD, y: yLimit },
];
const verticalThresholdUp = [
  { x: FC_THRESHOLD, y: 0 },
  { x: FC_THRESHOLD, y: yLimit },
];

function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        type: "line",
        label: "p = 0.05 cutoff",
        data: horizontalThreshold,
        borderColor: t.ink,
        borderDash: [8, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
      },
      {
        type: "line",
        label: "±2-fold cutoff",
        data: verticalThresholdDown,
        borderColor: t.ink,
        borderDash: [8, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
      },
      {
        type: "line",
        label: "±2-fold cutoff",
        data: verticalThresholdUp,
        borderColor: t.ink,
        borderDash: [8, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
      },
      {
        label: "Not significant",
        data: nonSigPoints,
        backgroundColor: withAlpha(INK_MUTED, 0.5),
        pointRadius: 3,
        pointHoverRadius: 3,
      },
      {
        label: "Down-regulated",
        data: downPoints,
        backgroundColor: withAlpha(t.palette[2], 0.65),
        pointRadius: 3.5,
        pointHoverRadius: 3.5,
      },
      {
        label: "Up-regulated",
        data: upPoints,
        backgroundColor: withAlpha(t.palette[4], 0.65),
        pointRadius: 3.5,
        pointHoverRadius: 3.5,
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
        text: "volcano-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => item.datasetIndex >= 3,
        },
      },
    },
    scales: {
      x: {
        min: -xLimit,
        max: xLimit,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "log2(Fold Change)",
          color: t.ink,
          font: { size: 18 },
        },
      },
      y: {
        min: 0,
        max: yLimit,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "-log10(p-value)",
          color: t.ink,
          font: { size: 18 },
        },
      },
    },
  },
});
