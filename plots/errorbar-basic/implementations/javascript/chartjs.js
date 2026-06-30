// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-30

const t = window.ANYPLOT_TOKENS;

// Temperature × plant growth study: mean stem length (cm) ± 1 SD across 5 conditions
const labels = ["15 °C", "20 °C", "25 °C", "30 °C", "35 °C"];
const means  = [12.3, 18.7, 24.2, 21.5, 16.1];
const errors = [2.1,  1.8,  2.3,  2.9,  3.4];

// Plugin: fill canvas with theme background before anything is drawn
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

// Plugin: I-bar error whiskers drawn over each bar after bars are rendered
const errorBarPlugin = {
  id: "errorBar",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const meta = chart.getDatasetMeta(0);
    const CAP = 18; // half-cap width in CSS px

    ctx.save();
    ctx.strokeStyle = t.ink;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "square";

    meta.data.forEach((bar, i) => {
      const x   = bar.x;
      const yHi = scales.y.getPixelForValue(means[i] + errors[i]);
      const yLo = scales.y.getPixelForValue(means[i] - errors[i]);

      // Vertical stem
      ctx.beginPath();
      ctx.moveTo(x, yHi);
      ctx.lineTo(x, yLo);
      ctx.stroke();

      // Top cap
      ctx.beginPath();
      ctx.moveTo(x - CAP, yHi);
      ctx.lineTo(x + CAP, yHi);
      ctx.stroke();

      // Bottom cap
      ctx.beginPath();
      ctx.moveTo(x - CAP, yLo);
      ctx.lineTo(x + CAP, yLo);
      ctx.stroke();
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
  plugins: [bgPlugin, errorBarPlugin],
  data: {
    labels,
    datasets: [
      {
        label: "Mean stem length (cm)",
        data: means,
        backgroundColor: t.palette[0] + "99", // brand green at ~60% opacity
        borderColor: t.palette[0],
        borderWidth: 2,
        borderRadius: 3,
        barPercentage: 0.55,
        categoryPercentage: 0.85,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 24, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: "errorbar-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 12, bottom: 18 },
      },
      legend: {
        labels: { color: t.inkSoft, font: { size: 16 }, boxWidth: 14 },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Growth Temperature",
          color: t.ink,
          font: { size: 15 },
        },
      },
      y: {
        min: 0,
        suggestedMax: 30,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Stem Length (cm)",
          color: t.ink,
          font: { size: 15 },
        },
      },
    },
  },
});
