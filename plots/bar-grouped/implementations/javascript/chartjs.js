// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-08-05

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

// --- Peak callout (custom Chart.js plugin, no external deps) -----------------
// Highlights the standout data point (Software, Q4) with a speech-bubble
// callout drawn directly on the canvas via the plugin lifecycle hooks.
const peakProduct = "Software";
const peakQuarterIndex = 3;
const peakValue = revenueByProduct[peakProduct][peakQuarterIndex];

const peakCalloutPlugin = {
  id: "peakCallout",
  afterDatasetsDraw(chart) {
    const datasetIndex = products.indexOf(peakProduct);
    const meta = chart.getDatasetMeta(datasetIndex);
    const bar = meta.data[peakQuarterIndex];
    if (!bar) return;

    const { ctx } = chart;
    const { x, y } = bar.getProps(["x", "y"], true);
    const label = `Peak: $${peakValue}M`;

    ctx.save();
    ctx.font = "600 16px sans-serif";
    const textWidth = ctx.measureText(label).width;
    const boxWidth = textWidth + 24;
    const boxHeight = 32;
    const boxX = x - boxWidth / 2;
    const boxY = y - boxHeight - 16;

    ctx.fillStyle = t.ink;
    ctx.beginPath();
    ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 6);
    ctx.moveTo(x - 7, boxY + boxHeight);
    ctx.lineTo(x + 7, boxY + boxHeight);
    ctx.lineTo(x, boxY + boxHeight + 9);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = t.pageBg;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, x, boxY + boxHeight / 2);
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: quarters,
    datasets: products.map((product, i) => ({
      label: product,
      data: revenueByProduct[product],
      backgroundColor: t.palette[i % t.palette.length],
      hoverBackgroundColor: t.palette[i % t.palette.length],
      borderWidth: 0,
      borderRadius: 4,
    })),
  },
  plugins: [peakCalloutPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 44, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "Quarterly Revenue by Product Line · bar-grouped · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        align: "start",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 18, boxHeight: 18, usePointStyle: true, pointStyle: "rect" },
      },
      tooltip: {
        callbacks: {
          label: (item) => `${item.dataset.label}: $${item.formattedValue}M`,
        },
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
        suggestedMax: 92,
      },
    },
  },
});
