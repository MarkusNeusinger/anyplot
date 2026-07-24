// anyplot.ai
// marimekko-basic: Basic Marimekko Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Revenue ($M) by region (drives bar width) and product line (drives the
// stacked share within each bar).
const regions = ["North America", "Europe", "Asia Pacific", "Latin America"];
const products = ["Hardware", "Software", "Services"];
const revenue = [
  [180, 220, 90], // North America
  [90, 140, 60], // Europe
  [60, 130, 40], // Asia Pacific
  [30, 50, 20], // Latin America
];
const regionTotals = revenue.map((row) => row.reduce((sum, v) => sum + v, 0));
const grandTotal = regionTotals.reduce((sum, v) => sum + v, 0);

// --- Layout: a fine category grid stands in for variable bar widths --------
// Chart.js sizes every bar in a dataset uniformly, so each region becomes a
// run of adjacent zero-gap grid slots proportional to its revenue share; a
// single blank slot between runs reads as the gap between mekko columns.
const GRID_UNITS = 100;
const columnWidths = regionTotals.map((total) => Math.round((total / grandTotal) * GRID_UNITS));
columnWidths[columnWidths.length - 1] += GRID_UNITS - columnWidths.reduce((a, b) => a + b, 0);

const labels = [];
const slotRegion = []; // region index per grid slot, -1 for a gap slot
regions.forEach((region, ri) => {
  const start = labels.length;
  for (let i = 0; i < columnWidths[ri]; i++) {
    labels.push("");
    slotRegion.push(ri);
  }
  labels[start + Math.floor(columnWidths[ri] / 2)] = region;
  if (ri < regions.length - 1) {
    labels.push("");
    slotRegion.push(-1);
  }
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: products.map((product, pi) => ({
      label: product,
      data: slotRegion.map((ri) => (ri === -1 ? 0 : (revenue[ri][pi] / regionTotals[ri]) * 100)),
      backgroundColor: t.palette[pi % t.palette.length],
      borderWidth: 0,
      barPercentage: 1,
      categoryPercentage: 1,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "marimekko-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 } },
      },
      tooltip: {
        filter: (item) => item.parsed.y > 0,
        callbacks: {
          title: (items) => regions[slotRegion[items[0].dataIndex]],
          label: (item) => {
            const ri = slotRegion[item.dataIndex];
            const value = revenue[ri][item.datasetIndex];
            return `${item.dataset.label}: $${value}M (${item.parsed.y.toFixed(0)}%)`;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: t.inkSoft, font: { size: 14 }, autoSkip: false, maxRotation: 0 },
        grid: { display: false },
        title: {
          display: true,
          text: "Region — bar width ∝ total revenue",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        stacked: true,
        min: 0,
        max: 100,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 25,
          callback: (value) => `${value}%`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Share of Region Revenue", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
