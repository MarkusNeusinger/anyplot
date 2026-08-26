// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Splitting-criterion curves across the full probability range [0, 1].
const POINTS = 100;
const probabilities = Array.from({ length: POINTS }, (_, i) => i / (POINTS - 1));

const log2 = (x) => Math.log(x) / Math.log(2);

const giniPoints = probabilities.map((p) => ({ x: p, y: 2 * p * (1 - p) }));
const entropyPoints = probabilities.map((p) => {
  // Edge cases: 0 * log2(0) is undefined, defined as 0 by convention.
  const term1 = p === 0 ? 0 : -p * log2(p);
  const term2 = p === 1 ? 0 : -(1 - p) * log2(1 - p);
  return { x: p, y: term1 + term2 };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom plugin: annotate the shared maximum at p = 0.5 -------------------
const maxImpurityAnnotation = {
  id: "maxImpurityAnnotation",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const x = scales.x.getPixelForValue(0.5);

    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 5]);
    ctx.beginPath();
    ctx.moveTo(x, chartArea.top);
    ctx.lineTo(x, chartArea.bottom);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = t.ink;
    ctx.font = "16px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Max impurity at p = 0.5", x, chartArea.top - 10);
    ctx.restore();
  },
};
Chart.register(maxImpurityAnnotation);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Gini Impurity: 2p(1-p)",
        data: giniPoints,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 4,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Entropy: -p·log₂(p) - (1-p)·log₂(1-p)",
        data: entropyPoints,
        borderColor: t.palette[1],
        backgroundColor: t.palette[1],
        borderWidth: 3,
        borderDash: [10, 6],
        pointRadius: 0,
        tension: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    plugins: {
      title: {
        display: true,
        text: "line-impurity-comparison · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 10, bottom: 34 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 1,
        title: { display: true, text: "Probability of Positive Class (p)", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 0.1 },
        grid: { display: false },
      },
      y: {
        min: 0,
        max: 1,
        title: { display: true, text: "Impurity Measure", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
});
