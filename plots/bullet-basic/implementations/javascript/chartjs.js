// anyplot.ai
// bullet-basic: Basic Bullet Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;
const theme = window.ANYPLOT_THEME || "light";

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly KPIs normalized to a common "% of target" scale so the bullets
// stay comparable at a glance, per anyplot's own dashboard-alignment note.
const metrics = [
  { name: "Revenue Growth", actual: 92, target: 100 },
  { name: "Customer Retention", actual: 105, target: 100 },
  { name: "Market Share", actual: 68, target: 100 },
  { name: "Net Promoter Score", actual: 130, target: 100 },
];
const ranges = [60, 85, 140]; // poor / satisfactory / good band boundaries

// Grayscale bands read as chrome (structural, not data) — built from the ink
// token so they stay theme-adaptive while staying strictly grayscale.
const inkRGB = theme === "light" ? "26,26,23" : "240,239,232";
const bandColors = [`rgba(${inkRGB},0.10)`, `rgba(${inkRGB},0.18)`, `rgba(${inkRGB},0.28)`];

const categories = metrics.map((m) => m.name);
const bandThickness = 70;
const actualThickness = 26;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom draw: target ticks + actual-value labels --------------------------
// Core Chart.js plugin API (afterDatasetsDraw hook) — no external plugin
// package, just canvas drawing keyed off the chart's own scale geometry.
const bulletExtrasPlugin = {
  id: "bulletExtras",
  afterDatasetsDraw(chart) {
    const { ctx, scales, chartArea } = chart;
    const goodMeta = chart.getDatasetMeta(0);
    const actualMeta = chart.getDatasetMeta(3);
    ctx.save();
    metrics.forEach((m, i) => {
      const row = goodMeta.data[i];
      const half = (row.height / 2) * 1.35;
      const targetX = scales.x.getPixelForValue(m.target);
      const top = Math.max(row.y - half, chartArea.top);
      const bottom = Math.min(row.y + half, chartArea.bottom);
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(targetX, top);
      ctx.lineTo(targetX, bottom);
      ctx.stroke();

      const bar = actualMeta.data[i];
      ctx.fillStyle = t.ink;
      ctx.font = "600 16px sans-serif";
      ctx.textBaseline = "middle";
      ctx.textAlign = "left";
      ctx.fillText(`${m.actual}%`, bar.x + 10, bar.y);
    });
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: categories,
    datasets: [
      {
        label: "Good",
        data: metrics.map(() => [ranges[1], ranges[2]]),
        backgroundColor: bandColors[2],
        barThickness: bandThickness,
        borderWidth: 0,
      },
      {
        label: "Satisfactory",
        data: metrics.map(() => [ranges[0], ranges[1]]),
        backgroundColor: bandColors[1],
        barThickness: bandThickness,
        borderWidth: 0,
      },
      {
        label: "Poor",
        data: metrics.map(() => [0, ranges[0]]),
        backgroundColor: bandColors[0],
        barThickness: bandThickness,
        borderWidth: 0,
      },
      {
        label: "Actual",
        data: metrics.map((m) => [0, m.actual]),
        backgroundColor: t.palette[0],
        barThickness: actualThickness,
        borderWidth: 0,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: 40 } },
    plugins: {
      title: {
        display: true,
        text: "Quarterly KPI Dashboard · bullet-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 16 },
          generateLabels: () => [
            { text: "Poor", fillStyle: bandColors[0], strokeStyle: bandColors[0], lineWidth: 0 },
            { text: "Satisfactory", fillStyle: bandColors[1], strokeStyle: bandColors[1], lineWidth: 0 },
            { text: "Good", fillStyle: bandColors[2], strokeStyle: bandColors[2], lineWidth: 0 },
            { text: "Actual", fillStyle: t.palette[0], strokeStyle: t.palette[0], lineWidth: 0 },
            { text: "Target", fillStyle: t.ink, strokeStyle: t.ink, lineWidth: 0 },
          ],
        },
      },
    },
    scales: {
      x: {
        min: 0,
        max: 150,
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}%` },
        grid: { color: t.grid },
        title: { display: true, text: "Percent of Quarterly Target", color: t.ink, font: { size: 16 } },
      },
      y: {
        grouped: false,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
    },
  },
  plugins: [bulletExtrasPlugin],
});
