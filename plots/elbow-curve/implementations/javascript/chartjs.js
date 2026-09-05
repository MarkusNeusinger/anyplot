// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer segmentation: K-means inertia across k=1..10 on behavioral features
// (purchase frequency, average order value, recency).
const kValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const inertia = [980, 560, 340, 230, 205, 188, 174, 163, 154, 147];
const optimalK = 4;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: kValues,
    datasets: [
      {
        label: "Inertia",
        data: inertia,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        pointRadius: 7,
        pointHoverRadius: 9,
        borderWidth: 3,
        cubicInterpolationMode: "monotone",
        tension: 0.3,
        fill: false,
      },
      {
        label: `Optimal k = ${optimalK}`,
        data: kValues.map((k) => (k === optimalK ? inertia[optimalK - 1] : null)),
        showLine: false,
        pointBackgroundColor: t.palette[1],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        pointRadius: 12,
        pointHoverRadius: 14,
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
        text: "elbow-curve · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true, pointStyle: "circle" },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Number of Clusters (k)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: { display: true, text: "Inertia (Within-Cluster Sum of Squares)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        beginAtZero: true,
      },
    },
  },
});
