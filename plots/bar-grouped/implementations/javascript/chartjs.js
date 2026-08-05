// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const products = ["Hardware", "Software", "Services"];
const revenueByProduct = {
  Hardware: [42, 38, 45, 51],
  Software: [61, 68, 72, 79],
  Services: [29, 33, 31, 37],
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: quarters,
    datasets: products.map((product, i) => ({
      label: product,
      data: revenueByProduct[product],
      backgroundColor: t.palette[i % t.palette.length],
      borderWidth: 0,
      borderRadius: 4,
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
        text: "Quarterly Revenue by Product Line · bar-grouped · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 18, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 18, boxHeight: 18, usePointStyle: true, pointStyle: "rect" },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Fiscal Quarter", color: t.ink, font: { size: 15 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `$${v}M` },
        grid: { color: t.grid },
        border: { display: false },
        title: { display: true, text: "Revenue (USD Millions)", color: t.ink, font: { size: 15 } },
        beginAtZero: true,
      },
    },
  },
});
