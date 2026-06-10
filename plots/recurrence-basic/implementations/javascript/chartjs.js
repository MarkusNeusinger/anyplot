// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-10

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Logistic map: x_{n+1} = r * x_n * (1 - x_n), chaotic regime r=3.9
const N = 200;
const r = 3.9;
const series = new Array(N);
series[0] = 0.4;
for (let i = 1; i < N; i++) {
  series[i] = r * series[i - 1] * (1 - series[i - 1]);
}

// Binary recurrence matrix — state pair (i,j) is recurrent when |x_i - x_j| < epsilon
const epsilon = 0.12;
const recMatrix = [];
for (let i = 0; i < N; i++) {
  recMatrix[i] = new Uint8Array(N);
  for (let j = 0; j < N; j++) {
    if (Math.abs(series[i] - series[j]) < epsilon) {
      recMatrix[i][j] = 1;
    }
  }
}

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Plugin: draw plot area background then the recurrence matrix before datasets layer
const recurrencePlugin = {
  id: "recurrenceMatrix",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea } = chart;
    const { left, top, right, bottom } = chartArea;
    const cellW = (right - left) / N;
    const cellH = (bottom - top) / N;

    ctx.save();

    // Plot area background
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(left, top, right - left, bottom - top);

    // Recurrent pairs in Imprint brand green
    ctx.fillStyle = t.palette[0];
    for (let i = 0; i < N; i++) {
      const x = left + i * cellW;
      for (let j = 0; j < N; j++) {
        if (recMatrix[i][j]) {
          // Canvas y increases downward; j=0 maps to bottom of chart area
          ctx.fillRect(x, top + (N - 1 - j) * cellH, cellW + 0.5, cellH + 0.5);
        }
      }
    }

    ctx.restore();
  },
};

new Chart(canvas, {
  type: "scatter",
  data: { datasets: [] },
  plugins: [recurrencePlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "recurrence-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 12, bottom: 18 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: N,
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 6 },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Time index i",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 8 },
        },
      },
      y: {
        type: "linear",
        min: 0,
        max: N,
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 6 },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Time index j",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 8 },
        },
      },
    },
  },
});
