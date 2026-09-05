// anyplot.ai
// funnel-basic: Basic Funnel Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// E-commerce checkout funnel: visitors thinning out at each subsequent step.
const stages = [
  "Website Visitors",
  "Product Page Views",
  "Added to Cart",
  "Checkout Started",
  "Purchase Completed",
];
const values = [12000, 6400, 3100, 1450, 820];

// Floating (centered) horizontal bars: each spans [-value/2, value/2], so
// stacking them by decreasing value produces the tapering funnel silhouette.
const segments = values.map((v) => [-v / 2, v / 2]);
const maxHalfWidth = values[0] / 2;
const colors = stages.map((_, i) => t.palette[i % t.palette.length]);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Segment label plugin (native Chart.js plugin API) ----------------------
// Draws the value + share-of-top-stage label centered inside each segment.
const segmentLabels = {
  id: "segmentLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "700 20px sans-serif";
    ctx.fillStyle = "#FFFFFF";
    ctx.shadowColor = "rgba(26, 26, 23, 0.5)";
    ctx.shadowBlur = 6;
    ctx.shadowOffsetY = 1;
    meta.data.forEach((bar, i) => {
      const { x, y } = bar.getCenterPoint();
      const share = Math.round((values[i] / values[0]) * 100);
      const label = `${values[i].toLocaleString()} (${share}%)`;
      ctx.fillText(label, x, y);
    });
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: stages,
    datasets: [
      {
        data: segments,
        backgroundColor: colors,
        borderColor: t.pageBg,
        borderWidth: 4,
        borderSkipped: false,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    barPercentage: 0.94,
    categoryPercentage: 0.86,
    plugins: {
      title: {
        display: true,
        text: "funnel-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 24 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        display: false,
        min: -maxHalfWidth * 1.05,
        max: maxHalfWidth * 1.05,
        grid: { display: false },
        border: { display: false },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { display: false },
        border: { display: false },
      },
    },
  },
  plugins: [segmentLabels],
});
