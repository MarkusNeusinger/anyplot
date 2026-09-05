// anyplot.ai
// histogram-density: Density Histogram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

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
        backgroundColor: t.palette[0],
        borderWidth: 0,
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
        font: { size: 22 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 } },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
        grid: { display: false },
        title: { display: true, text: "Resting Heart Rate (bpm)", color: t.ink, font: { size: 18 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Density", color: t.ink, font: { size: 18 } },
        beginAtZero: true,
      },
    },
  },
});
