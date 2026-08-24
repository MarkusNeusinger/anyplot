// anyplot.ai
// bump-basic: Basic Bump Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Streaming platform weekly top-6 popularity ranking (lower rank = more popular)
const weeks = ["Wk 1", "Wk 2", "Wk 3", "Wk 4", "Wk 5", "Wk 6", "Wk 7", "Wk 8"];
const platforms = [
  { name: "Netflix", ranks: [1, 1, 2, 2, 1, 1, 1, 1] },
  { name: "Disney+", ranks: [3, 2, 1, 1, 2, 2, 3, 2] },
  { name: "Max", ranks: [2, 3, 3, 4, 4, 3, 2, 3] },
  { name: "Prime Video", ranks: [4, 4, 4, 3, 3, 4, 4, 4] },
  { name: "Apple TV+", ranks: [6, 6, 5, 5, 5, 5, 5, 5] },
  { name: "Paramount+", ranks: [5, 5, 6, 6, 6, 6, 6, 6] },
];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: weeks,
    datasets: platforms.map((platform, i) => ({
      label: platform.name,
      data: platform.ranks,
      borderColor: t.palette[i % t.palette.length],
      backgroundColor: t.palette[i % t.palette.length],
      borderWidth: 3.5,
      pointRadius: 7,
      pointHoverRadius: 7,
      pointBackgroundColor: t.palette[i % t.palette.length],
      pointBorderColor: t.pageBg,
      pointBorderWidth: 2,
      tension: 0,
      fill: false,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "bump-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "right",
        labels: { color: t.ink, font: { size: 14 }, boxWidth: 16, boxHeight: 16 },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Week", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
      y: {
        reverse: true,
        min: 1,
        max: platforms.length,
        ticks: {
          stepSize: 1,
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `#${value}`,
        },
        title: { display: true, text: "Rank", color: t.ink, font: { size: 16 } },
        grid: { color: t.grid },
      },
    },
  },
});
