// anyplot.ai
// bar-error: Bar Chart with Error Bars
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Plant height (cm) by fertilizer treatment, error bars show +/-1 SD.
const treatments = ["Control", "Nitrogen", "Phosphorus", "Potassium", "N+P", "NPK Combined"];
const heights = [24.5, 31.2, 27.8, 26.1, 34.6, 39.8];
const stdDevs = [2.1, 2.8, 2.3, 2.0, 3.1, 3.4];

const maxWithError = Math.max(...heights.map((h, i) => h + stdDevs[i]));

// --- Error bar plugin (native Chart.js plugin API, drawn on canvas) --------
const errorBarsPlugin = {
  id: "errorBars",
  afterDatasetsDraw(chart) {
    const { ctx, scales: { y } } = chart;
    const meta = chart.getDatasetMeta(0);
    const capWidth = 16;

    ctx.save();
    ctx.strokeStyle = t.ink;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";

    meta.data.forEach((bar, i) => {
      const xCenter = bar.x;
      const yTop = y.getPixelForValue(heights[i] + stdDevs[i]);
      const yBottom = y.getPixelForValue(heights[i] - stdDevs[i]);

      ctx.beginPath();
      ctx.moveTo(xCenter, yTop);
      ctx.lineTo(xCenter, yBottom);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(xCenter - capWidth / 2, yTop);
      ctx.lineTo(xCenter + capWidth / 2, yTop);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(xCenter - capWidth / 2, yBottom);
      ctx.lineTo(xCenter + capWidth / 2, yBottom);
      ctx.stroke();
    });

    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: treatments,
    datasets: [
      {
        label: "Mean Plant Height",
        data: heights,
        backgroundColor: t.palette[0],
        borderWidth: 0,
        barPercentage: 0.6,
      },
    ],
  },
  plugins: [errorBarsPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 20 } },
    plugins: {
      title: {
        display: true,
        text: "bar-error · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 8 },
      },
      subtitle: {
        display: true,
        text: "Error bars show ±1 standard deviation across replicate plots",
        color: t.inkSoft,
        font: { size: 16 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Fertilizer Treatment", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        suggestedMax: Math.ceil(maxWithError * 1.1),
        title: { display: true, text: "Plant Height (cm)", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
});
