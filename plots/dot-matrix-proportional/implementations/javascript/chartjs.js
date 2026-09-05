// anyplot.ai
// dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
// Theme-adaptive "muted" semantic anchor (default-style-guide.md) — the
// browser harness token set does not expose it, so it is derived here.
const MUTED = t.theme === "light" ? "#6B6A63" : "#A8A79F";

// --- Data (in-memory, deterministic) ----------------------------------------
// Survey: "Should the city expand the downtown bike-lane network?"
const total = 100;
const cols = 10;
const rows = 10;
const categories = [
  { label: "Agreed", count: 47, color: t.palette[0] }, // positive sentiment -> brand green
  { label: "Disagreed", count: 34, color: t.palette[4] }, // negative sentiment -> semantic red
  { label: "No opinion", count: 19, color: MUTED }, // neutral sentiment -> muted anchor
];

// Assign each of the `total` grid cells to a category, filled in category
// order, left-to-right then top-to-bottom.
const dotIndexToCategory = new Array(total);
let cursor = 0;
categories.forEach((cat, catIndex) => {
  for (let i = 0; i < cat.count; i += 1) {
    dotIndexToCategory[cursor] = catIndex;
    cursor += 1;
  }
});

const datasets = categories.map((cat, catIndex) => {
  const points = [];
  for (let i = 0; i < total; i += 1) {
    if (dotIndexToCategory[i] !== catIndex) continue;
    const row = Math.floor(i / cols);
    const col = i % cols;
    points.push({ x: col, y: rows - 1 - row });
  }
  return {
    label: `${cat.label} (${cat.count})`,
    data: points,
    backgroundColor: cat.color,
    borderColor: t.pageBg,
    borderWidth: 1.5,
    pointStyle: "circle",
    pointRadius: 30,
    pointHoverRadius: 30,
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, bottom: 8, left: 8, right: 8 } },
    plugins: {
      title: {
        display: true,
        text: "dot-matrix-proportional · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          padding: 24,
        },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: -0.7,
        max: cols - 0.3,
        display: false,
      },
      y: {
        type: "linear",
        min: -0.7,
        max: rows - 0.3,
        display: false,
      },
    },
  },
});
