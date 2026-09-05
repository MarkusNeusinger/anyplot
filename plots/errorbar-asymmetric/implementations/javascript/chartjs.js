// anyplot.ai
// errorbar-asymmetric: Asymmetric Error Bars Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: projected revenue growth by segment, with asymmetric 90% CI -----
// (upside risk differs from downside risk — financial forecasting scenario)
const segments = [
  "Cloud Services",
  "Hardware",
  "Consulting",
  "Retail",
  "Subscriptions",
  "Licensing",
  "Advertising",
  "Logistics",
];
const growth = [8.4, 2.1, 4.6, -1.2, 9.8, 3.0, 6.8, 0.4];
const errorLower = [2.5, 1.8, 3.2, 3.0, 3.0, 1.4, 4.0, 2.0];
const errorUpper = [4.5, 1.2, 2.0, 2.1, 5.5, 1.0, 2.3, 1.5];

// Y-range must cover the error bars themselves, not just the point values —
// Chart.js autoscales to the scatter dataset, which the plugin's manually
// drawn whiskers fall outside of unless the axis bounds account for them.
const bounds = growth.flatMap((g, i) => [g - errorLower[i], g + errorUpper[i]]);
const yPad = (Math.max(...bounds) - Math.min(...bounds)) * 0.08;
const yMin = Math.floor(Math.min(...bounds) - yPad);
const yMax = Math.ceil(Math.max(...bounds) + yPad);

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom plugin: draws asymmetric error bars (vertical whisker + caps) --
// Chart.js has no built-in error-bar chart type; the documented pattern for
// this is a plugin hooked into afterDatasetsDraw that reads pixel positions
// from the chart's own scales — no external error-bar library involved.
const errorBarPlugin = {
  id: "asymmetricErrorBars",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const meta = chart.getDatasetMeta(0);
    const capHalfWidth = 14;
    ctx.save();
    ctx.strokeStyle = t.palette[0];
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    meta.data.forEach((point, i) => {
      const x = point.x;
      const yTop = scales.y.getPixelForValue(growth[i] + errorUpper[i]);
      const yBottom = scales.y.getPixelForValue(growth[i] - errorLower[i]);
      // whisker
      ctx.beginPath();
      ctx.moveTo(x, yTop);
      ctx.lineTo(x, yBottom);
      ctx.stroke();
      // caps
      ctx.beginPath();
      ctx.moveTo(x - capHalfWidth, yTop);
      ctx.lineTo(x + capHalfWidth, yTop);
      ctx.moveTo(x - capHalfWidth, yBottom);
      ctx.lineTo(x + capHalfWidth, yBottom);
      ctx.stroke();
    });
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Projected growth (10th–90th percentile)",
        data: segments.map((_, i) => ({ x: i, y: growth[i] })),
        backgroundColor: t.pageBg,
        borderColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 9,
        pointHoverRadius: 9,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 30, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: "errorbar-asymmetric · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        display: true,
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 15 },
          usePointStyle: true,
          pointStyle: "circle",
          padding: 16,
        },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: -0.5,
        max: segments.length - 0.5,
        // Force one tick per category at exact integer positions — a linear
        // scale's default "nice number" tick placement does not otherwise
        // land on the integers segments[] is indexed by.
        afterBuildTicks: (axis) => {
          axis.ticks = segments.map((_, i) => ({ value: i }));
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => segments[value] ?? "",
        },
        grid: { display: false },
        title: { display: true, text: "Business Segment", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: yMin,
        max: yMax,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `${value}%`,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Projected Revenue Growth (%)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
  plugins: [errorBarPlugin],
});
