// anyplot.ai
// histogram-density: Density Histogram
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Resting heart rate (bpm) for 600 adults, ~Normal(mean=72, std=8).
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const n = 600;
const mean = 72;
const std = 8;
const samples = [];
for (let i = 0; i < n; i++) {
  const u1 = rand();
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  samples.push(mean + std * z);
}

const binCount = 24;
const dataMin = Math.min(...samples);
const dataMax = Math.max(...samples);
const binWidth = (dataMax - dataMin) / binCount;

const counts = new Array(binCount).fill(0);
for (const value of samples) {
  const idx = Math.min(binCount - 1, Math.floor((value - dataMin) / binWidth));
  counts[idx]++;
}

// Normalize so total bar area equals 1 (density, not raw count).
const density = counts.map((c) => c / (n * binWidth));
const binCenters = Array.from(
  { length: binCount },
  (_, i) => dataMin + (i + 0.5) * binWidth,
);
const labels = binCenters.map((c) => c.toFixed(1));

// Theoretical normal PDF evaluated at each bin center.
const normalPdf = (x) =>
  Math.exp(-0.5 * ((x - mean) / std) ** 2) / (std * Math.sqrt(2 * Math.PI));
const pdfValues = binCenters.map(normalPdf);

// Goodness-of-fit residual per bin, used to scriptably shade bars: bins that
// tightly track the theoretical curve render fully saturated, bins that
// deviate render lighter — a visual callout for the fit without extra chrome.
const residuals = density.map((d, i) => Math.abs(d - pdfValues[i]));
const maxResidual = Math.max(...residuals) || 1;

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        type: "bar",
        label: "Empirical density",
        data: density,
        backgroundColor: (ctx) => {
          const i = ctx.dataIndex;
          if (i === undefined) return t.palette[0];
          const fit = 1 - residuals[i] / maxResidual;
          return hexToRgba(t.palette[0], 0.45 + 0.55 * fit);
        },
        borderWidth: 0,
        borderRadius: 2,
        categoryPercentage: 1.0,
        barPercentage: 1.0,
        order: 2,
      },
      {
        type: "line",
        label: "Normal PDF (theoretical)",
        data: pdfValues,
        borderColor: t.palette[1],
        backgroundColor: "transparent",
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.35,
        fill: false,
        order: 1,
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
        text: "histogram-density · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          boxWidth: 24,
          boxHeight: 12,
          padding: 20,
          generateLabels: (chart) =>
            chart.data.datasets.map((ds, i) => ({
              text: ds.label,
              datasetIndex: i,
              hidden: !chart.isDatasetVisible(i),
              pointStyle: ds.type === "line" ? "line" : "rect",
              fillStyle: ds.type === "line" ? ds.borderColor : t.palette[0],
              strokeStyle: ds.type === "line" ? ds.borderColor : t.palette[0],
              lineWidth: ds.type === "line" ? 3 : 0,
            })),
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            if (ctx.dataset.type === "bar") {
              const z = ((binCenters[ctx.dataIndex] - mean) / std).toFixed(2);
              return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)} (z = ${z})`;
            }
            return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 12,
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Resting Heart Rate (bpm)",
          color: t.ink,
          font: { size: 18 },
        },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Density",
          color: t.ink,
          font: { size: 18 },
        },
        beginAtZero: true,
      },
    },
  },
});
