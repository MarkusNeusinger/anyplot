// anyplot.ai
// ma-differential-expression: MA Plot for Differential Expression
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-21
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Seeded LCG pseudo-random number generator (deterministic, no Math.random)
function lcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// Box-Muller transform: uniform -> standard normal
function randn(rng) {
  const u = rng() + 1e-10;
  const v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// --- Data ------------------------------------------------------------------
const rng = lcg(42);
const genes = [];

// 4000 background genes: noise increases at low expression levels
for (let i = 0; i < 4000; i++) {
  const a = 0.5 + Math.pow(rng(), 0.65) * 13.5;
  const sigma = 0.12 + 0.55 * Math.exp(-a / 4.5);
  const bias = -0.28 * Math.exp(-a / 2.8);
  const m = randn(rng) * sigma + bias;
  genes.push({ a, m });
}

// 500 true differentially expressed genes (medium-high expression)
const rng2 = lcg(7919);
for (let i = 0; i < 500; i++) {
  const a = 2.5 + rng2() * 10;
  const up = rng2() > 0.45;
  const m = (up ? 1 : -1) * (1.8 + rng2() * 2.5) + randn(rng2) * 0.35;
  genes.push({ a, m });
}

// Classify by |M| > 1.5 significance threshold
const notSig = [], sigUp = [], sigDown = [];
genes.forEach(({ a, m }) => {
  if (m > 1.5) sigUp.push({ x: a, y: m });
  else if (m < -1.5) sigDown.push({ x: a, y: m });
  else notSig.push({ x: a, y: m });
});

// --- LOESS smooth (tricube kernel, bandwidth = 2.5 A-units) ----------------
const smooth = Array.from({ length: 51 }, (_, i) => {
  const ax = 0.5 + (14.0 / 50) * i;
  let ws = 0, wt = 0;
  genes.forEach(({ a, m }) => {
    const d = Math.abs(a - ax) / 2.5;
    if (d < 1) {
      const w = Math.pow(1 - d * d * d, 3);
      ws += w * m;
      wt += w;
    }
  });
  return wt > 2 ? { x: ax, y: ws / wt } : null;
}).filter(Boolean);

// --- Reference lines -------------------------------------------------------
const refZero = [{ x: 0.2, y: 0 }, { x: 14.8, y: 0 }];
const refPos1 = [{ x: 0.2, y: 1 }, { x: 14.8, y: 1 }];
const refNeg1 = [{ x: 0.2, y: -1 }, { x: 14.8, y: -1 }];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
const TITLE = "ma-differential-expression · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Not significant (" + notSig.length + ")",
        data: notSig,
        backgroundColor: t.inkSoft + "2E",
        borderWidth: 0,
        pointRadius: 1.5,
        pointHoverRadius: 2.5,
      },
      {
        label: "Up-regulated (" + sigUp.length + ")",
        data: sigUp,
        backgroundColor: t.palette[0] + "CC",
        borderWidth: 0,
        pointRadius: 3.5,
        pointHoverRadius: 5,
      },
      {
        label: "Down-regulated (" + sigDown.length + ")",
        data: sigDown,
        backgroundColor: "#AE3030CC",
        borderWidth: 0,
        pointRadius: 3.5,
        pointHoverRadius: 5,
      },
      {
        label: "M = 0",
        type: "line",
        data: refZero,
        borderColor: t.ink + "99",
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
      },
      {
        label: "±1 fold change",
        type: "line",
        data: refPos1,
        borderColor: t.inkSoft + "77",
        borderWidth: 1.5,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
      },
      {
        label: "",
        type: "line",
        data: refNeg1,
        borderColor: t.inkSoft + "77",
        borderWidth: 1.5,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
      },
      {
        label: "LOESS trend",
        type: "line",
        data: smooth,
        borderColor: t.palette[2],
        borderWidth: 4,
        pointRadius: 0,
        fill: false,
        tension: 0.3,
        spanGaps: false,
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
        text: TITLE,
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 10, bottom: 14 },
      },
      legend: {
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 14 },
          usePointStyle: true,
          filter: (item) => item.text !== "",
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 15,
        title: {
          display: true,
          text: "A: Mean Average Expression (log₂)",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 8 },
        },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        type: "linear",
        min: -7,
        max: 7,
        title: {
          display: true,
          text: "M: Log₂ Fold Change",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 8 },
        },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        border: { display: false },
      },
    },
  },
});
