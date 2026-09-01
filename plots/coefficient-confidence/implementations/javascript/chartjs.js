// anyplot.ai
// coefficient-confidence: Coefficient Plot with Confidence Intervals
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-01

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
// `muted` (other/rest/confidence-band-fill anchor) isn't in ANYPLOT_TOKENS —
// derive it from the theme per the style guide's theme-adaptive value.
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Standardized coefficients from a multiple linear regression predicting
// house sale price, ordered by |coefficient| descending.
const rows = [
  { variable: "Square Footage", coefficient: 42.8, ciLower: 36.1, ciUpper: 49.5, significant: true },
  { variable: "Distance to City Center (mi)", coefficient: -31.4, ciLower: -39.2, ciUpper: -23.6, significant: true },
  { variable: "Bathrooms", coefficient: 24.6, ciLower: 16.3, ciUpper: 32.9, significant: true },
  { variable: "Age of Home (years)", coefficient: -19.7, ciLower: -28.5, ciUpper: -10.9, significant: true },
  { variable: "Garage Spaces", coefficient: 16.2, ciLower: 7.4, ciUpper: 25.0, significant: true },
  { variable: "Lot Size (acres)", coefficient: 11.5, ciLower: 2.1, ciUpper: 20.9, significant: true },
  { variable: "Bedrooms", coefficient: 7.8, ciLower: -2.6, ciUpper: 18.2, significant: false },
  { variable: "Renovated Kitchen", coefficient: 5.3, ciLower: -4.9, ciUpper: 15.5, significant: false },
];

const labels = rows.map((row) => row.variable);
const ciRanges = rows.map((row) => [row.ciLower, row.ciUpper]);
const significantEstimates = rows.map((row) => (row.significant ? [row.coefficient - 0.35, row.coefficient + 0.35] : null));
const notSignificantEstimates = rows.map((row) => (row.significant ? null : [row.coefficient - 0.35, row.coefficient + 0.35]));
const zeroLine = labels.map((label) => ({ x: 0, y: label }));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "95% Confidence Interval",
        data: ciRanges,
        backgroundColor: MUTED + "55",
        borderWidth: 0,
        barThickness: 6,
        borderSkipped: false,
      },
      {
        type: "line",
        label: "Zero effect",
        data: zeroLine,
        borderColor: t.inkSoft,
        borderWidth: 2,
        borderDash: [8, 6],
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: "Significant (95% CI excludes 0)",
        data: significantEstimates,
        backgroundColor: t.palette[0],
        borderWidth: 0,
        barThickness: 20,
        borderRadius: 10,
        borderSkipped: false,
      },
      {
        label: "Not significant",
        data: notSignificantEstimates,
        backgroundColor: MUTED,
        borderWidth: 0,
        barThickness: 20,
        borderRadius: 10,
        borderSkipped: false,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "coefficient-confidence · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 15 }, boxWidth: 24, padding: 18 },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Coefficient Estimate ($1,000s per unit, standardized)", color: t.ink, font: { size: 17 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        ticks: { color: t.ink, font: { size: 15 } },
        grid: { display: false },
      },
    },
  },
});
