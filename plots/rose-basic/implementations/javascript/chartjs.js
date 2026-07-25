// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-25

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
        borderWidth: 2,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    startAngle: 0,
    plugins: {
      title: {
        display: true,
        text: "rose-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
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
        grid: { color: t.grid },
        angleLines: { color: t.grid },
        pointLabels: {
          display: true,
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
