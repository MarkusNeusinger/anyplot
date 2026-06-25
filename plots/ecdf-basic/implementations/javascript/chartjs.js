// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// LCG for reproducible pseudo-random numbers (no seeded RNG in the browser)
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) & 0xffffffff;
  return (seed >>> 0) / 0xffffffff;
}
function randNormal(mean, std) {
  const u1 = lcg() + 1e-10;
  const u2 = lcg();
  return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Marathon finish times (minutes) — novice vs experienced runners
const N = 200;
const noviceTimes = Array.from({ length: N }, () => randNormal(265, 35));
const experiencedTimes = Array.from({ length: N }, () => randNormal(225, 25));

// ECDF: sort values and compute cumulative proportions (i+1)/n
function computeECDF(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const range = sorted[sorted.length - 1] - sorted[0];
  const ecdf = sorted.map((x, i) => ({ x, y: (i + 1) / sorted.length }));
  ecdf.unshift({ x: sorted[0] - range * 0.03, y: 0 });
  return ecdf;
}

const noviceECDF = computeECDF(noviceTimes);
const experiencedECDF = computeECDF(experiencedTimes);

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Background plugin — fills canvas with pageBg before all drawing
const bgPlugin = {
  id: "bg",
  beforeDraw(chart) {
    const { ctx } = chart;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  },
};

new Chart(canvas, {
  type: "line",
  plugins: [bgPlugin],
  data: {
    datasets: [
      {
        label: "Novice Runners",
        data: noviceECDF,
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        borderWidth: 3,
        stepped: "before",
        pointRadius: 0,
      },
      {
        label: "Experienced Runners",
        data: experiencedECDF,
        borderColor: t.palette[1],
        backgroundColor: "transparent",
        borderWidth: 3,
        stepped: "before",
        pointRadius: 0,
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
        text: "ecdf-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 20 },
      },
    },
    scales: {
      x: {
        type: "linear",
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Finish Time (minutes)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        min: 0,
        max: 1,
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Cumulative Proportion",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (v) => v.toFixed(1),
        },
        grid: { color: t.grid },
      },
    },
  },
});
