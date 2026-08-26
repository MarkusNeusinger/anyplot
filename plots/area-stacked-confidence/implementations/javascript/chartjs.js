// anyplot.ai
// area-stacked-confidence: Stacked Area Chart with Confidence Bands
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-26

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Reproducible pseudo-randomness (browser has no seeded RNG) ------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Data: quarterly revenue forecast by product line, with 90% prediction
// intervals that widen further into the forecast horizon -------------------
const quarterCount = 20;
const labels = Array.from({ length: quarterCount }, (_, q) => {
  const year = 2024 + Math.floor(q / 4);
  const quarter = (q % 4) + 1;
  return `Q${quarter} ${year}`;
});

const productLines = [
  { name: "Hardware", base: 38, growth: 0.028 },
  { name: "Software", base: 24, growth: 0.052 },
  { name: "Services", base: 14, growth: 0.038 },
];

// Central forecast values per product line, with mild multiplicative noise.
const centralValues = productLines.map((line) =>
  Array.from({ length: quarterCount }, (_, q) => {
    const trend = line.base * Math.pow(1 + line.growth, q);
    const noise = 1 + (rand() - 0.5) * 0.06;
    return trend * noise;
  })
);

// Prediction-interval half-width grows with forecast horizon (more
// uncertainty further out) and scales with the series' own magnitude.
const bandHalfWidths = centralValues.map((series) =>
  series.map((value, q) => value * (0.05 + 0.009 * q))
);

// Stack the central values, then carry the same cumulative base into each
// series' band so bounds stay consistent with the stack order (Notes).
const cumulativeBase = productLines.map(() => new Array(quarterCount).fill(0));
for (let q = 0; q < quarterCount; q += 1) {
  let running = 0;
  for (let i = 0; i < productLines.length; i += 1) {
    cumulativeBase[i][q] = running;
    running += centralValues[i][q];
  }
}

const cumulativeCentral = productLines.map((_, i) =>
  centralValues[i].map((value, q) => cumulativeBase[i][q] + value)
);
const cumulativeLower = productLines.map((_, i) =>
  centralValues[i].map((value, q) => cumulativeBase[i][q] + value - bandHalfWidths[i][q])
);
const cumulativeUpper = productLines.map((_, i) =>
  centralValues[i].map((value, q) => cumulativeBase[i][q] + value + bandHalfWidths[i][q])
);

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Datasets: stacked central areas first (bottom to top), then their
// confidence bands layered on top as translucent ribbons -------------------
const centralDatasets = productLines.map((line, i) => ({
  label: line.name,
  data: cumulativeCentral[i],
  borderColor: t.palette[i],
  backgroundColor: hexToRgba(t.palette[i], 0.65),
  borderWidth: 2.5,
  pointRadius: 0,
  tension: 0,
  fill: i === 0 ? "origin" : i - 1,
  isBand: false,
}));

const bandDatasets = [];
productLines.forEach((line, i) => {
  const upperIndex = centralDatasets.length + bandDatasets.length;
  bandDatasets.push({
    label: `${line.name} interval upper`,
    data: cumulativeUpper[i],
    borderWidth: 0,
    pointRadius: 0,
    fill: false,
    isBand: true,
  });
  bandDatasets.push({
    label: `${line.name} interval lower`,
    data: cumulativeLower[i],
    borderColor: "transparent",
    backgroundColor: hexToRgba(t.palette[i], 0.3),
    borderWidth: 0,
    pointRadius: 0,
    fill: upperIndex,
    isBand: true,
  });
});

// --- Chart -------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [...centralDatasets, ...bandDatasets],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { intersect: false },
    plugins: {
      title: {
        display: true,
        text: "area-stacked-confidence · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 6 },
      },
      subtitle: {
        display: true,
        text: "Shaded bands show the 90% prediction interval for each product line",
        color: t.inkSoft,
        font: { size: 14 },
        padding: { bottom: 16 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item, data) => !data.datasets[item.datasetIndex].isBand,
        },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10 },
        grid: { display: false },
        title: { display: true, text: "Fiscal Quarter", color: t.ink, font: { size: 16 } },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Cumulative Revenue ($M)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
