// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Quarterly revenue by product line, in $M.
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const productLines = ["Hardware", "Software", "Services"];
const revenueByProduct = [
  [4.2, 4.6, 5.1, 6.0], // Hardware
  [3.1, 3.6, 4.0, 4.8], // Software
  [1.8, 2.0, 2.3, 2.7], // Services
];
const totals = quarters.map((_, i) => revenueByProduct.reduce((sum, series) => sum + series[i], 0));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Total-label plugin ------------------------------------------------------
// Core Chart.js has no built-in data-label rendering; drawing text in an
// `afterDatasetsDraw` hook is the idiomatic Chart.js way to annotate bars
// (documented pattern, not a third-party plugin).
const totalLabelsPlugin = {
  id: "totalLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const meta = chart.getDatasetMeta(chart.data.datasets.length - 1);
    ctx.save();
    ctx.font = "bold 18px -apple-system, sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    meta.data.forEach((bar, i) => {
      const label = `$${totals[i].toFixed(1)}M`;
      ctx.fillText(label, bar.x, scales.y.getPixelForValue(totals[i]) - 10);
    });
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: quarters,
    datasets: productLines.map((name, i) => ({
      label: name,
      data: revenueByProduct[i],
      backgroundColor: t.palette[i],
      borderWidth: 0,
      stack: "revenue",
    })),
  },
  plugins: [totalLabelsPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { top: 40 },
    },
    plugins: {
      title: {
        display: true,
        text: "bar-stacked-labeled · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 15 }, boxWidth: 18 },
      },
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Quarter", color: t.ink, font: { size: 16 } },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        suggestedMax: Math.max(...totals) * 1.15,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `$${value}M`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Revenue ($M)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
