// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-02

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG for reproducible scatter data (seed = 42)
let seed = 42;
const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0x100000000; };

// Data: Annual rainfall (mm) vs wheat yield (t/ha) across 150 agricultural regions
// Positive correlation r ≈ 0.7 with realistic noise
const n = 150;
const points = Array.from({ length: n }, () => {
  const rainfall = 250 + rand() * 750;
  const baseline = 1.2 + ((rainfall - 250) / 750) * 4.2;
  const yield_val = baseline + (rand() - 0.5) * 4.0;
  return { x: +rainfall.toFixed(1), y: +Math.max(0.2, yield_val).toFixed(2) };
});

// Canvas background plugin — fills with pageBg so dark theme renders correctly
const bgPlugin = {
  id: "canvasBg",
  beforeDraw(chart) {
    const { ctx, width, height } = chart;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  },
};

// Mount canvas into the harness container
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Chart
new Chart(canvas, {
  type: "scatter",
  plugins: [bgPlugin],
  data: {
    datasets: [{
      label: "Agricultural Region",
      data: points,
      backgroundColor: t.palette[0] + "b3",  // Imprint brand green at 70% opacity
      borderColor: t.pageBg,
      borderWidth: 1.5,
      pointRadius: 6,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 16, right: 48, bottom: 16, left: 16 } },
    plugins: {
      title: {
        display: true,
        text: "scatter-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 32, weight: "normal" },
        padding: { top: 8, bottom: 20 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 18 }, maxTicksLimit: 8 },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Annual Rainfall (mm)",
          color: t.ink,
          font: { size: 22 },
          padding: { top: 8 },
        },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 18 } },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Wheat Yield (t/ha)",
          color: t.ink,
          font: { size: 22 },
          padding: { bottom: 8 },
        },
      },
    },
  },
});
