// anyplot.ai
// lollipop-grouped: Grouped Lollipop Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue ($M) by product line, across four sales regions.
const regions = ["North America", "Europe", "Asia Pacific", "Latin America"];
const productLines = ["Hardware", "Software", "Services"];
const revenueByProduct = [
  [42.5, 31.8, 24.2, 15.6], // Hardware
  [38.1, 35.4, 29.7, 12.3], // Software
  [21.6, 19.2, 16.8, 9.1], // Services
];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom plugin: draws the lollipop dot on top of each thin stem bar ------
// Chart.js has no native lollipop controller; drawing the marker with a plugin
// keeps every dataset a plain "bar" so the category scale's built-in grouped
// offset positions the stems (and therefore the dots) for us.
const lollipopDots = {
  id: "lollipopDots",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    chart.data.datasets.forEach((dataset, datasetIndex) => {
      const meta = chart.getDatasetMeta(datasetIndex);
      meta.data.forEach((bar) => {
        const { x, y } = bar.getProps(["x", "y"], true);
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.fillStyle = dataset.backgroundColor;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = t.pageBg;
        ctx.stroke();
        ctx.restore();
      });
    });
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: regions,
    datasets: productLines.map((label, i) => ({
      label,
      data: revenueByProduct[i],
      backgroundColor: t.palette[i],
      barThickness: 10,
      borderRadius: 5,
      borderSkipped: false,
      categoryPercentage: 0.7,
      barPercentage: 0.9,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 20, right: 20 } },
    plugins: {
      title: {
        display: true,
        text: "lollipop-grouped · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 24 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 16,
          boxHeight: 16,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.grid },
        title: {
          display: true,
          text: "Region",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        border: { display: false },
        title: {
          display: true,
          text: "Quarterly Revenue ($M)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
  plugins: [lollipopDots],
});
