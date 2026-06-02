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

// Focal-point treatment: brand green for the top performer, muted ink for the
// rest. Spec explicitly invites "highlight specific bars to draw attention".
const maxIdx = revenue.indexOf(Math.max(...revenue));
const barColors = revenue.map((_, i) =>
  i === maxIdx ? t.palette[0] : t.inkSoft,
);
const hoverColors = revenue.map((_, i) =>
  i === maxIdx ? t.palette[0] : t.ink,
);

// Custom Chart.js plugin — draws each bar's value just above its top edge so
// readers can pick up the exact figure without hovering. Uses theme-adaptive
// ink and a heavier weight on the leader so it reads as the focal point.
const valueLabels = {
  id: "valueLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    meta.data.forEach((bar, i) => {
      const isLeader = i === maxIdx;
      ctx.fillStyle = isLeader ? t.palette[0] : t.inkSoft;
      ctx.font = `${isLeader ? 600 : 500} ${isLeader ? 18 : 15}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
      ctx.fillText(revenue[i].toFixed(1), bar.x, bar.y - 8);
    });
    ctx.restore();
  },
};

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
        backgroundColor: barColors,
        hoverBackgroundColor: hoverColors,
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
    layout: { padding: { top: 36, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "bar-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 4, bottom: 24 },
      },
      legend: { display: false },
      tooltip: {
        backgroundColor: t.elevatedBg,
        titleColor: t.ink,
        bodyColor: t.inkSoft,
        borderColor: t.grid,
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 14, weight: "600" },
        bodyFont: { size: 13 },
        displayColors: false,
        callbacks: {
          label: (ctx) => `$${ctx.parsed.y.toFixed(1)} million`,
        },
      },
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
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        title: {
          display: true,
          text: "Revenue (USD millions)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 12 },
        },
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { color: t.grid, drawTicks: false },
        border: { display: false },
        beginAtZero: true,
      },
    },
  },
  plugins: [valueLabels],
});
