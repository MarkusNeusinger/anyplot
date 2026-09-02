// anyplot.ai
// area-stacked-percent: 100% Stacked Area Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Smartphone OS market share, 2015-2024 — raw unit counts normalized to a
// percentage of the yearly total so every stack sums to exactly 100%.
const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
const rawByCategory = {
  Android: [713, 780, 850, 917, 965, 1001, 1027, 1041, 1057, 1072],
  iOS: [161, 192, 231, 273, 315, 342, 362, 381, 400, 417],
  "Windows Phone": [161, 120, 81, 39, 13, 3, 0, 0, 0, 0],
  BlackBerry: [81, 66, 38, 20, 7, 0, 0, 0, 0, 0],
  Other: [34, 42, 50, 51, 40, 34, 31, 28, 23, 21],
};

const categories = Object.keys(rawByCategory);
const yearlyTotals = years.map((_, i) =>
  categories.reduce((sum, cat) => sum + rawByCategory[cat][i], 0),
);
const shareByCategory = {};
categories.forEach((cat) => {
  shareByCategory[cat] = rawByCategory[cat].map(
    (v, i) => (v / yearlyTotals[i]) * 100,
  );
});

const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const datasets = categories.map((cat, i) => ({
  label: cat,
  data: shareByCategory[cat],
  backgroundColor: hexToRgba(t.palette[i % t.palette.length], 0.75),
  borderColor: t.palette[i % t.palette.length],
  // Dominant series (Android) gets a heavier stroke as the focal emphasis.
  borderWidth: i === 0 ? 3 : 1.5,
  pointRadius: 0,
  // Straight segments guarantee the 100%-stacked bands never overshoot
  // between the 10 sampled years (a spline could dip below 0 or over 100).
  tension: 0,
  fill: i === 0 ? "origin" : "-1",
}));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
const title =
  "Smartphone OS Market Share · area-stacked-percent · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "line",
  data: { labels: years, datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: 17, weight: "500" },
        padding: { bottom: 6 },
      },
      subtitle: {
        display: true,
        text: "Annual global shipment share across five platforms, 2015-2024",
        color: t.inkSoft,
        font: { size: 13, weight: "400", style: "italic" },
        padding: { bottom: 18 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 20, padding: 16 },
      },
      filler: { propagate: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Year", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
      y: {
        stacked: true,
        min: 0,
        max: 100,
        title: {
          display: true,
          text: "Market Share (%)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 20,
          callback: (value) => `${value}%`,
        },
        grid: { color: t.grid, borderDash: [3, 4] },
      },
    },
  },
});
