// anyplot.ai
// learning-curve-basic: Model Learning Curve
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Data (in-memory, deterministic) ----------------------------------------
// Digit-classifier learning curve: mean +/- 1 std across 8 cross-validation
// folds, evaluated at 10 training-set sizes.
const trainSizes = [90, 180, 360, 540, 720, 900, 1080, 1260, 1440, 1617];
const trainMean = [0.999, 0.998, 0.995, 0.992, 0.99, 0.988, 0.987, 0.986, 0.985, 0.984];
const trainStd = [0.002, 0.003, 0.004, 0.004, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005];
const valMean = [0.87, 0.905, 0.928, 0.941, 0.949, 0.954, 0.958, 0.961, 0.963, 0.965];
const valStd = [0.035, 0.03, 0.025, 0.022, 0.02, 0.018, 0.017, 0.016, 0.015, 0.015];

const trainUpper = trainMean.map((m, i) => m + trainStd[i]);
const trainLower = trainMean.map((m, i) => m - trainStd[i]);
const valUpper = valMean.map((m, i) => m + valStd[i]);
const valLower = valMean.map((m, i) => m - valStd[i]);

const trainColor = t.palette[0]; // brand green
const valColor = t.palette[1]; // lavender

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
// Confidence bands are drawn first (as fill-only line pairs, hidden from the
// legend), then the mean lines are drawn on top so the bands sit behind them.
new Chart(canvas, {
  type: "line",
  data: {
    labels: trainSizes,
    datasets: [
      {
        label: "Training ±1 SD",
        data: trainUpper,
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: "Training ±1 SD",
        data: trainLower,
        borderWidth: 0,
        pointRadius: 0,
        backgroundColor: hexToRgba(trainColor, 0.18),
        fill: "-1",
        tension: 0.3,
      },
      {
        label: "Validation ±1 SD",
        data: valUpper,
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: "Validation ±1 SD",
        data: valLower,
        borderWidth: 0,
        pointRadius: 0,
        backgroundColor: hexToRgba(valColor, 0.18),
        fill: "-1",
        tension: 0.3,
      },
      {
        label: "Training score",
        data: trainMean,
        borderColor: trainColor,
        backgroundColor: trainColor,
        pointBackgroundColor: trainColor,
        borderWidth: 3.5,
        pointRadius: 5,
        fill: false,
        tension: 0.3,
      },
      {
        label: "Validation score",
        data: valMean,
        borderColor: valColor,
        backgroundColor: valColor,
        pointBackgroundColor: valColor,
        borderWidth: 3.5,
        pointRadius: 5,
        fill: false,
        tension: 0.3,
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
        text: "learning-curve-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => !item.text.includes("±1 SD"),
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Training Set Size (samples)", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: 0.8,
        max: 1.0,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Cross-Validation Accuracy", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
