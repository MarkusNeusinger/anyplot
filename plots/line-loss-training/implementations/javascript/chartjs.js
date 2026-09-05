// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: chartjs 4.4.7 | JavaScript 22.23.3
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: train/validation cross-entropy loss over 60 epochs ---------------
// Deterministic — no RNG needed, both curves are closed-form functions of epoch.
const EPOCHS = 60;
const epochs = [];
const trainLoss = [];
const valLoss = [];
for (let e = 1; e <= EPOCHS; e++) {
  epochs.push(e);
  trainLoss.push(2.6 * Math.exp(-0.085 * e) + 0.06 + 0.015 * Math.sin(e * 0.9));
  // Validation loss tracks training loss early on, then overfitting sets in:
  // a slow quadratic climb overtakes the exponential decay past ~epoch 30.
  valLoss.push(2.7 * Math.exp(-0.07 * e) + 0.00033 * (e - 1) ** 2 + 0.09 + 0.02 * Math.sin(e * 0.7 + 1));
}

// --- Optimal early-stopping point: epoch with minimum validation loss -------
let minIdx = 0;
for (let i = 1; i < valLoss.length; i++) {
  if (valLoss[i] < valLoss[minIdx]) minIdx = i;
}
const stopEpoch = epochs[minIdx];
const stopLoss = valLoss[minIdx];

// --- Mount --------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: epochs,
    datasets: [
      {
        label: "Training loss",
        data: trainLoss,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        tension: 0.15,
      },
      {
        label: "Validation loss",
        data: valLoss,
        borderColor: t.palette[2],
        backgroundColor: t.palette[2],
        borderWidth: 3.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        tension: 0.15,
      },
      {
        label: `Early-stopping point (epoch ${stopEpoch})`,
        type: "scatter",
        data: [{ x: stopEpoch, y: stopLoss }],
        backgroundColor: t.amber,
        borderColor: t.ink,
        borderWidth: 2,
        pointRadius: 10,
        pointHoverRadius: 12,
        pointStyle: "circle",
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 24, right: 32, bottom: 12, left: 12 } },
    plugins: {
      title: {
        display: true,
        text: "line-loss-training · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24, weight: "500" },
        padding: { top: 8, bottom: 24 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true, padding: 24 },
      },
      tooltip: {
        backgroundColor: t.elevatedBg,
        titleColor: t.ink,
        bodyColor: t.inkSoft,
        borderColor: t.grid,
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 16 },
        bodyFont: { size: 14 },
      },
    },
    scales: {
      x: {
        type: "linear",
        title: { display: true, text: "Epoch", color: t.ink, font: { size: 20 }, padding: { top: 14 } },
        ticks: { color: t.inkSoft, font: { size: 16 }, stepSize: 10 },
        grid: { display: false },
        border: { color: t.grid },
        min: 1,
        max: EPOCHS,
      },
      y: {
        title: {
          display: true,
          text: "Cross-Entropy Loss",
          color: t.ink,
          font: { size: 20 },
          padding: { bottom: 14 },
        },
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { color: t.grid, drawTicks: false },
        border: { display: false },
        beginAtZero: true,
      },
    },
    interaction: { mode: "nearest", intersect: false },
  },
});
