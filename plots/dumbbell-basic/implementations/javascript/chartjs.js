// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-06-30

const t = window.ANYPLOT_TOKENS;

// Training scores before and after a skills development program (10 departments)
const rawData = [
  { dept: "Legal",       before: 65, after: 72 },
  { dept: "Admin",       before: 58, after: 68 },
  { dept: "Finance",     before: 69, after: 83 },
  { dept: "HR",          before: 70, after: 86 },
  { dept: "Marketing",   before: 74, after: 90 },
  { dept: "Support",     before: 61, after: 78 },
  { dept: "Operations",  before: 57, after: 75 },
  { dept: "Sales",       before: 63, after: 81 },
  { dept: "Product",     before: 72, after: 91 },
  { dept: "Engineering", before: 68, after: 88 },
];

// Sort ascending by improvement so the largest gain appears at the top of the chart
rawData.sort((a, b) => (a.after - a.before) - (b.after - b.before));

const labels     = rawData.map(d => d.dept);
const beforeData = rawData.map((d, i) => ({ x: d.before, y: i }));
const afterData  = rawData.map((d, i) => ({ x: d.after,  y: i }));

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Plugin: fill full canvas with theme background
const bgPlugin = {
  id: "background",
  beforeDraw(chart) {
    const ctx = chart.ctx;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  },
};

// Plugin: draw dumbbell connecting lines behind the dots
const dumbbellPlugin = {
  id: "dumbbell",
  beforeDatasetsDraw(chart) {
    const ctx   = chart.ctx;
    const meta0 = chart.getDatasetMeta(0); // Before points
    const meta1 = chart.getDatasetMeta(1); // After points

    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth   = 2.5;
    ctx.globalAlpha = 0.55;
    ctx.lineCap     = "round";

    for (let i = 0; i < meta0.data.length; i++) {
      const p0 = meta0.data[i];
      const p1 = meta1.data[i];
      if (!p0 || !p1) continue;
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
    }
    ctx.restore();
  },
};

// Chart
new Chart(canvas, {
  type: "scatter",
  plugins: [bgPlugin, dumbbellPlugin],
  data: {
    datasets: [
      {
        label: "Before Program",
        data: beforeData,
        backgroundColor: t.palette[0],  // #009E73 brand green — Imprint pos 1
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: 11,
        pointHoverRadius: 13,
        clip: false,
      },
      {
        label: "After Program",
        data: afterData,
        backgroundColor: t.palette[1],  // #C475FD lavender — Imprint pos 2
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: 11,
        pointHoverRadius: 13,
        clip: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "dumbbell-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 16, bottom: 18 },
      },
      legend: {
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 18,
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Training Score",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 8 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { color: t.grid },
        min: 50,
        max: 100,
      },
      y: {
        type: "linear",
        min: -0.5,
        max: rawData.length - 0.5,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 1,
          callback(value) {
            const idx = Math.round(value);
            return labels[idx] !== undefined ? labels[idx] : "";
          },
        },
        grid: { color: t.grid },
      },
    },
    layout: {
      padding: { left: 10, right: 24, top: 8, bottom: 12 },
    },
  },
});
