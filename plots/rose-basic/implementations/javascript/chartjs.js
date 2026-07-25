// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 95/100 | Created: 2026-07-25

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Annual wind direction frequency at a coastal station — prevailing westerlies.
// N and NW (the two wedges touching the top radial axis) are kept in the same
// tick band on purpose: Chart.js draws the r-scale's numeric labels only along
// that top axis, and an opaque wedge reaching past a ring on just one side of
// it visually eats half the label — keeping both wedges below the 10% ring
// avoids that split.
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const frequencyPct = [8, 11, 9, 6, 15, 19, 24, 8];
const dominantDirection = "W";

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "polarArea",
  data: {
    labels: directions,
    datasets: [
      {
        data: frequencyPct,
        backgroundColor: t.palette,
        borderColor: t.pageBg,
        // Scriptable width: give the prevailing direction (W, 24%) a heavier
        // outline so the "prevailing wind" takeaway reads at a glance.
        borderWidth: (ctx) =>
          directions[ctx.dataIndex] === dominantDirection ? 5 : 2,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    startAngle: 0,
    layout: { padding: 24 },
    plugins: {
      title: {
        display: true,
        text: "rose-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24, weight: "bold" },
        padding: { bottom: 4 },
      },
      subtitle: {
        display: true,
        text: "Prevailing wind: W (24%) → SW (19%) → S (15%)",
        color: t.inkSoft,
        font: { size: 15, style: "italic" },
        padding: { bottom: 16 },
      },
      legend: { display: false },
    },
    scales: {
      r: {
        beginAtZero: true,
        ticks: {
          color: t.inkSoft,
          backdropColor: "transparent",
          font: { size: 14 },
          callback: (value) => `${value}%`,
        },
        grid: { color: t.grid, lineWidth: 1, circular: true },
        angleLines: { color: t.grid, lineWidth: 1 },
        pointLabels: {
          display: true,
          color: t.ink,
          font: (ctx) => ({
            size: 16,
            weight:
              directions[ctx.index] === dominantDirection ? "bold" : "normal",
          }),
        },
      },
    },
  },
});
