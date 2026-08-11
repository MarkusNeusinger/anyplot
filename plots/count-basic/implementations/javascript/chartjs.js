// anyplot.ai
// count-basic: Basic Count Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data: raw categorical observations, counted client-side --------------
// (mirrors a countplot / value_counts() workflow rather than pre-aggregated bars)
function lcg(seed) {
  let state = seed;
  return function () {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const categories = [
  "Billing",
  "Technical",
  "Shipping",
  "Account",
  "Feature Request",
  "Other",
];
const weights = [0.27, 0.24, 0.18, 0.15, 0.11, 0.05];
const cumulative = weights.reduce((acc, w) => {
  acc.push((acc.length ? acc[acc.length - 1] : 0) + w);
  return acc;
}, []);

const ticketCount = 320;
const counts = new Map(categories.map((category) => [category, 0]));
for (let i = 0; i < ticketCount; i++) {
  const r = rand();
  const idx = cumulative.findIndex((c) => r <= c);
  const category = categories[idx === -1 ? categories.length - 1 : idx];
  counts.set(category, counts.get(category) + 1);
}

const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
const labels = sorted.map(([label]) => label);
const values = sorted.map(([, value]) => value);

// Pareto overlay: running share of all tickets covered as categories are
// added left-to-right along the descending sort. This is the spec's own
// "optional percentage annotations" note, expressed as a genuine Chart.js
// mixed-type dataset (bar + line, dual y-axis) rather than a plain % label.
let runningTotal = 0;
const cumulativeShare = values.map((value) => {
  runningTotal += value;
  return (runningTotal / ticketCount) * 100;
});

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Distinctive Chart.js touches -------------------------------------------
// Top-to-bottom alpha falloff on each bar (same brand hue in both themes, only
// the gradient stop opacity differs), a custom draw plugin that renders the
// exact count above every bar, and a mixed bar+line dataset (dual y-axis) that
// overlays the Pareto cumulative-share curve from the second Imprint color.
function barGradient(context) {
  const { chart } = context;
  const { ctx, chartArea } = chart;
  if (!chartArea) return t.palette[0];
  const gradient = ctx.createLinearGradient(
    0,
    chartArea.top,
    0,
    chartArea.bottom,
  );
  gradient.addColorStop(0, t.palette[0]);
  gradient.addColorStop(1, `${t.palette[0]}99`);
  return gradient;
}

const countLabelPlugin = {
  id: "countLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = "600 15px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    // Halo stroke in the page background color keeps the label legible even
    // where the cumulative-share line crosses behind it (data-dependent, so
    // the crossing point can't be avoided by fixed positioning alone).
    ctx.strokeStyle = t.pageBg;
    ctx.lineWidth = 4;
    ctx.lineJoin = "round";
    ctx.fillStyle = t.ink;
    meta.data.forEach((bar, i) => {
      const text = String(chart.data.datasets[0].data[i]);
      ctx.strokeText(text, bar.x, bar.y - 8);
      ctx.fillText(text, bar.x, bar.y - 8);
    });
    ctx.restore();
  },
};

// --- Chart --------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        type: "bar",
        label: "Support Tickets",
        data: values,
        backgroundColor: barGradient,
        borderRadius: 4,
        maxBarThickness: 140,
        categoryPercentage: 0.85,
        barPercentage: 0.9,
        yAxisID: "count",
      },
      {
        type: "line",
        label: "Cumulative Share",
        data: cumulativeShare,
        borderColor: t.palette[1],
        backgroundColor: t.palette[1],
        borderWidth: 2,
        borderDash: [6, 4],
        pointRadius: 4,
        pointBackgroundColor: t.palette[1],
        tension: 0.25,
        yAxisID: "percentage",
      },
    ],
  },
  plugins: [countLabelPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 40, right: 10, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: "count-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 6 },
      },
      subtitle: {
        display: true,
        text: `n = ${ticketCount} tickets`,
        color: t.inkSoft,
        font: { size: 14, style: "italic" },
        padding: { bottom: 24 },
      },
      legend: {
        display: true,
        labels: { color: t.ink, font: { size: 14 }, boxWidth: 22 },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Support Ticket Category",
          color: t.ink,
          font: { size: 16 },
        },
      },
      count: {
        type: "linear",
        position: "left",
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 }, precision: 0 },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Count",
          color: t.ink,
          font: { size: 16 },
        },
      },
      percentage: {
        type: "linear",
        position: "right",
        min: 0,
        max: 100,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `${value}%`,
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Cumulative Share",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
