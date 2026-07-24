// anyplot.ai
// parallel-basic: Basic Parallel Coordinates Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic, iris-inspired) ------------------------
// Tiny fixed-seed LCG + Box-Muller so the sample is reproducible without
// Math.random (the browser has no seeded RNG).
let lcgSeed = 42;
function lcgRand() {
  lcgSeed = (lcgSeed * 1103515245 + 12345) & 0x7fffffff;
  return lcgSeed / 0x7fffffff;
}
function randNormal() {
  const u1 = Math.max(lcgRand(), 1e-9);
  const u2 = lcgRand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const dimensions = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"];

// Approximate per-species mean/sd for each dimension (cm), iris-inspired.
const speciesStats = [
  { name: "Setosa", stats: [[5.0, 0.35], [3.42, 0.38], [1.46, 0.17], [0.24, 0.11]] },
  { name: "Versicolor", stats: [[5.94, 0.52], [2.77, 0.31], [4.26, 0.47], [1.33, 0.2]] },
  { name: "Virginica", stats: [[6.59, 0.64], [2.97, 0.32], [5.55, 0.55], [2.03, 0.27]] },
];
const OBS_PER_SPECIES = 20;

const observations = [];
speciesStats.forEach((species, speciesIndex) => {
  for (let i = 0; i < OBS_PER_SPECIES; i++) {
    const raw = species.stats.map(([mean, sd]) => mean + sd * randNormal());
    observations.push({ speciesIndex, raw });
  }
});

// Min-max normalize each dimension independently so all axes share one 0-1
// scale and can be compared side by side, per the spec's normalization note.
const mins = dimensions.map((_, d) => Math.min(...observations.map((o) => o.raw[d])));
const maxs = dimensions.map((_, d) => Math.max(...observations.map((o) => o.raw[d])));
observations.forEach((o) => {
  o.normalized = o.raw.map((v, d) => (v - mins[d]) / (maxs[d] - mins[d]));
});

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const speciesColors = speciesStats.map((_, i) => t.palette[i % t.palette.length]);

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
// One line dataset per observation (Chart.js has no native parallel-coords
// type); category x-axis ticks stand in for the per-dimension axes, and a
// shared normalized y-axis keeps every dimension comparable.
new Chart(canvas, {
  type: "line",
  data: {
    labels: dimensions,
    datasets: observations.map((o) => ({
      data: o.normalized,
      borderColor: hexToRgba(speciesColors[o.speciesIndex], 0.5),
      borderWidth: 1.75,
      pointRadius: 0,
      pointHoverRadius: 0,
      tension: 0,
      fill: false,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "parallel-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 24,
          generateLabels: () =>
            speciesStats.map((species, i) => ({
              text: species.name,
              fillStyle: speciesColors[i],
              strokeStyle: speciesColors[i],
              lineWidth: 2,
              datasetIndex: i * OBS_PER_SPECIES,
            })),
        },
        onClick: () => {},
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "category",
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.ink, lineWidth: 1.5, tickLength: 0 },
      },
      y: {
        min: 0,
        max: 1,
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 0.25 },
        grid: { display: false },
        title: {
          display: true,
          text: "Normalized Value (min–max scaled per dimension)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
