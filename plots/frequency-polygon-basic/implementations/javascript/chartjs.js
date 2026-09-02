// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reaction times (ms) recorded across three experimental conditions in a
// psychology response-time study.
function makeLcg(seed) {
  let state = seed;
  return function lcg() {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function normalSamples(rng, n, mean, std) {
  const samples = [];
  for (let i = 0; i < n; i += 2) {
    const u1 = Math.max(rng(), 1e-9);
    const u2 = rng();
    const mag = std * Math.sqrt(-2 * Math.log(u1));
    samples.push(mean + mag * Math.cos(2 * Math.PI * u2));
    samples.push(mean + mag * Math.sin(2 * Math.PI * u2));
  }
  return samples.slice(0, n);
}

const rng = makeLcg(42);
const groups = [
  { name: "Control", n: 300, mean: 480, std: 55 },
  { name: "Caffeine", n: 260, mean: 420, std: 48 },
  { name: "Sleep-deprived", n: 240, mean: 545, std: 70 },
];
const groupSamples = groups.map((g) => normalSamples(rng, g.n, g.mean, g.std));

// Shared bin edges across all groups for accurate comparison
const binWidth = 25;
const allValues = groupSamples.flat();
const minVal = Math.floor(Math.min(...allValues) / binWidth) * binWidth;
const maxVal = Math.ceil(Math.max(...allValues) / binWidth) * binWidth;
const binCount = Math.round((maxVal - minVal) / binWidth);

function frequencyPolygon(samples) {
  const counts = new Array(binCount).fill(0);
  samples.forEach((v) => {
    const idx = Math.min(Math.max(Math.floor((v - minVal) / binWidth), 0), binCount - 1);
    counts[idx] += 1;
  });
  const midpoints = counts.map((_, i) => minVal + (i + 0.5) * binWidth);
  // Extend to zero at both ends to close the polygon shape
  const points = [{ x: midpoints[0] - binWidth, y: 0 }];
  counts.forEach((c, i) => points.push({ x: midpoints[i], y: c }));
  points.push({ x: midpoints[midpoints.length - 1] + binWidth, y: 0 });
  return points;
}

const groupPoints = groupSamples.map((samples) => frequencyPolygon(samples));
const dashPatterns = [[], [10, 6], [3, 4]];

const datasets = groups.map((g, i) => {
  const points = groupPoints[i];
  return {
    label: g.name,
    data: points,
    borderColor: t.palette[i],
    backgroundColor: `${t.palette[i]}26`,
    borderDash: dashPatterns[i % dashPatterns.length],
    borderWidth: 3,
    fill: true,
    tension: 0,
    pointRadius: points.map((_, idx) => (idx === 0 || idx === points.length - 1 ? 0 : 4)),
    pointBackgroundColor: t.palette[i],
    pointBorderColor: t.pageBg,
    pointBorderWidth: 1,
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    plugins: {
      title: {
        display: true,
        text: "frequency-polygon-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: minVal - binWidth / 2,
        max: maxVal + binWidth / 2,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Reaction Time (ms)", color: t.ink, font: { size: 16 } },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Frequency (count)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
