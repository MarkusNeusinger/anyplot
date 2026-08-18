// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Small LCG PRNG + Box-Muller transform — the browser has no seeded RNG.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randomNormal(mean, stdDev) {
  const u1 = 1 - lcgRandom();
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const groups = [
  { name: "Morning Section", mean: 72, stdDev: 11, n: 300 },
  { name: "Afternoon Section", mean: 79, stdDev: 9, n: 300 },
];
groups.forEach((group) => {
  group.scores = Array.from({ length: group.n }, () =>
    Math.min(100, Math.max(0, randomNormal(group.mean, group.stdDev))),
  );
});

// --- Shared bins across both groups (aligned edges for a fair comparison) --
const allScores = groups.flatMap((group) => group.scores);
const binWidth = 5;
const minEdge = Math.floor(Math.min(...allScores) / binWidth) * binWidth;
const maxEdge = Math.ceil(Math.max(...allScores) / binWidth) * binWidth;
const binCount = (maxEdge - minEdge) / binWidth;
const binLabels = Array.from(
  { length: binCount },
  (_, i) => `${minEdge + i * binWidth}`,
);

groups.forEach((group) => {
  const counts = new Array(binCount).fill(0);
  group.scores.forEach((score) => {
    const idx = Math.min(
      binCount - 1,
      Math.max(0, Math.floor((score - minEdge) / binWidth)),
    );
    counts[idx] += 1;
  });
  group.counts = counts;
});

function withAlpha(hex, alpha) {
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
  type: "bar",
  data: {
    labels: binLabels,
    datasets: groups.map((group, i) => ({
      label: group.name,
      data: group.counts,
      backgroundColor: withAlpha(t.palette[i], 0.55),
      borderColor: t.palette[i],
      borderWidth: 1.5,
      barPercentage: 1.0,
      categoryPercentage: 1.0,
      grouped: false,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "histogram-overlapping · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 20 },
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          maxRotation: 0,
          autoSkipPadding: 12,
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Exam Score",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Number of Students",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
