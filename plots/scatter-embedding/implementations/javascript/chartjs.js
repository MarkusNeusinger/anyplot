// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-08-11

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated UMAP projection of PBMC (peripheral blood mononuclear cell)
// scRNA-seq profiles: 8 immune cell-type clusters, each an isotropic Gaussian
// blob around a hand-placed 2D centroid (mimics how related cell types sit
// closer together in a real embedding, e.g. lymphocytes on one side).
function makeLcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const clusters = [
  { label: "T cells", cx: -20, cy: 14, sx: 6, sy: 5 },
  { label: "B cells", cx: -28, cy: -10, sx: 5, sy: 6 },
  { label: "NK cells", cx: -6, cy: 24, sx: 4, sy: 4 },
  { label: "Monocytes", cx: 16, cy: 20, sx: 7, sy: 6 },
  { label: "Dendritic cells", cx: 30, cy: 6, sx: 5, sy: 5 },
  { label: "Neutrophils", cx: 24, cy: -16, sx: 6, sy: 5 },
  { label: "Erythrocytes", cx: -10, cy: -26, sx: 6, sy: 7 },
  { label: "Platelets", cx: 4, cy: -6, sx: 4, sy: 4 },
];
const pointsPerCluster = 80;

const datasets = clusters.map((cluster, i) => ({
  label: cluster.label,
  data: Array.from({ length: pointsPerCluster }, () => ({
    x: cluster.cx + gaussian() * cluster.sx,
    y: cluster.cy + gaussian() * cluster.sy,
  })),
  backgroundColor: hexToRgba(t.palette[i % t.palette.length], 0.65),
  borderWidth: 0,
  pointRadius: 4,
  pointHoverRadius: 4,
}));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 8, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "PBMC Cell Types · scatter-embedding · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 21, weight: "500" },
        padding: { bottom: 4 },
      },
      subtitle: {
        display: true,
        text: "UMAP projection (n_neighbors=15, min_dist=0.1)",
        color: t.inkSoft,
        font: { size: 16, style: "italic" },
        padding: { bottom: 16 },
      },
      legend: {
        position: "right",
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          usePointStyle: true,
          pointStyle: "circle",
          boxWidth: 8,
          boxHeight: 8,
          padding: 14,
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "UMAP 1", color: t.ink, font: { size: 16 } },
        ticks: { display: false },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
      y: {
        title: { display: true, text: "UMAP 2", color: t.ink, font: { size: 16 } },
        ticks: { display: false },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
    },
  },
});
