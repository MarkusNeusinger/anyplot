// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Data — quarterly revenue (USD millions) by product line
const labels = [
  "Apparel",
  "Footwear",
  "Accessories",
  "Equipment",
  "Eyewear",
  "Wellness",
];
const revenue = [42.8, 51.3, 18.9, 33.7, 12.4, 27.1];

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Chart
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Revenue (USD millions)",
        data: revenue,
        backgroundColor: t.palette[0], // #009E73 — Imprint brand green (single series)
        borderWidth: 0,
        borderRadius: 4,
        categoryPercentage: 0.72,
        barPercentage: 0.92,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "bar-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 4, bottom: 24 },
      },
      legend: { display: false },
      tooltip: { enabled: true },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Product line",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 12 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.grid },
      },
      y: {
        title: {
          display: true,
          text: "Revenue (USD millions)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 12 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid, drawTicks: false },
        border: { display: false },
        beginAtZero: true,
      },
    },
  },
});
