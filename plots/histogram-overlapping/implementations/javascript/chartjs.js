// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-18

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
  { name: "Morning Section", mean: 72, stdDev: 13, n: 300 },
  { name: "Afternoon Section", mean: 80, stdDev: 6, n: 300 },
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

// --- Mean-marker plugin --------------------------------------------------
// Makes the score-gap insight explicit: a dashed vertical line + label at
// each group's mean, positioned via the shared bin grid (fractional
// category index) so it lines up with the actual score, not the bin edge.
const meanMarkerPlugin = {
  id: "meanMarkers",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const xScale = scales.x;
    ctx.save();
    groups.forEach((group, i) => {
      const fracIndex = (group.mean - minEdge) / binWidth - 0.5;
      const xPixel = xScale.getPixelForValue(fracIndex);

      ctx.strokeStyle = t.palette[i];
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(xPixel, chartArea.top);
      ctx.lineTo(xPixel, chartArea.bottom);
      ctx.stroke();

      ctx.setLineDash([]);
      ctx.fillStyle = t.palette[i];
      ctx.font = "600 13px sans-serif";
      ctx.textAlign = i === 0 ? "right" : "left";
      ctx.fillText(
        `mean ${group.mean.toFixed(0)}`,
        xPixel + (i === 0 ? -6 : 6),
        chartArea.top + 16,
      );
    });
    ctx.restore();
  },
};

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
  plugins: [meanMarkerPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { right: 24, top: 8 },
    },
    plugins: {
      title: {
        display: true,
        text: "histogram-overlapping · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          boxWidth: 14,
          usePointStyle: true,
          pointStyle: "rectRounded",
        },
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
