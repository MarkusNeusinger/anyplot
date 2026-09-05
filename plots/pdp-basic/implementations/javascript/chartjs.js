// anyplot.ai
// pdp-basic: Partial Dependence Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Partial dependence of predicted house price on living-area square footage,
// as if extracted from a GradientBoostingRegressor. The effect is centered at
// zero at the median square footage so the curve reads as a relative lift.
const GRID_POINTS = 60;
const SQFT_MIN = 500;
const SQFT_MAX = 4000;
const SQFT_MEDIAN = 1500;

const featureValues = Array.from(
  { length: GRID_POINTS },
  (_, i) => SQFT_MIN + (i * (SQFT_MAX - SQFT_MIN)) / (GRID_POINTS - 1),
);

// Diminishing-returns effect (log-shaped), in thousands of dollars, zeroed at
// the median so the plot shows relative lift rather than absolute price.
const partialDependence = featureValues.map(
  (sqft) => 62 * Math.log(sqft / SQFT_MEDIAN),
);

// Uncertainty widens away from the bulk of the training data (fewer nearby
// samples at the tails), a standard PDP confidence-band shape.
const bandHalfWidth = featureValues.map((sqft) => {
  const distance = Math.abs(sqft - SQFT_MEDIAN) / (SQFT_MAX - SQFT_MIN);
  return 4 + 34 * distance * distance;
});
const upperBound = partialDependence.map((pd, i) => pd + bandHalfWidth[i]);
const lowerBound = partialDependence.map((pd, i) => pd - bandHalfWidth[i]);

// Rug: a small fixed-seed LCG stands in for the square-footage distribution
// of the training sample, clustered around the median with a long right tail.
let seed = 42;
const lcg = () => {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
};
const trainingSqft = Array.from({ length: 90 }, () => {
  const u1 = lcg() || 1e-9;
  const u2 = lcg();
  const gaussian = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const sample = SQFT_MEDIAN + gaussian * 420 + 260;
  return Math.min(SQFT_MAX - 20, Math.max(SQFT_MIN + 20, sample));
}).sort((a, b) => a - b);
const rugPoints = trainingSqft.map((sqft) => ({ x: sqft, y: 0.08 }));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart --------------------------------------------------------------------
const title = "House Price vs. Square Footage · pdp-basic · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Upper bound",
        data: featureValues.map((x, i) => ({ x, y: upperBound[i] })),
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: "95% confidence band",
        data: featureValues.map((x, i) => ({ x, y: lowerBound[i] })),
        borderWidth: 0,
        pointRadius: 0,
        backgroundColor: `${t.palette[0]}26`,
        fill: "-1",
        tension: 0.3,
      },
      {
        label: "Partial dependence",
        data: featureValues.map((x, i) => ({ x, y: partialDependence[i] })),
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 4,
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: "Training data (rug)",
        type: "scatter",
        data: rugPoints,
        yAxisID: "rug",
        pointStyle: "line",
        rotation: 90,
        radius: 9,
        borderColor: t.inkSoft,
        borderWidth: 1.5,
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 30, bottom: 10, left: 10 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: 19, weight: "500" } },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          filter: (item) => item.text === "Partial dependence" || item.text === "95% confidence band",
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: SQFT_MIN,
        max: SQFT_MAX,
        title: { display: true, text: "Living Area (sq ft)", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: { display: true, text: "Partial Dependence ($k, centered)", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      rug: {
        type: "linear",
        position: "left",
        display: false,
        min: 0,
        max: 1,
      },
    },
  },
});
