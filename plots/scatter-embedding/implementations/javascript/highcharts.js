// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-11
//# anyplot-orientation: landscape
// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data: UMAP projection of customer-support ticket embeddings -----------
// Deterministic LCG so the layout is reproducible across renders.
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = Math.max(nextRandom(), 1e-9);
  const u2 = nextRandom();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const clusters = [
  { name: "Billing", center: [-6, 4], spread: 1.1, symbol: "circle" },
  { name: "Shipping", center: [5, 5], spread: 1.3, symbol: "diamond" },
  { name: "Product Quality", center: [0, -1], spread: 1.6, symbol: "triangle" },
  { name: "Account Access", center: [-6.5, -4.5], spread: 1.0, symbol: "square" },
  { name: "Returns", center: [6, -4.5], spread: 1.2, symbol: "triangle-down" },
];

const pointsPerCluster = 120; // 600 points total — within the spec's 500-5000 range

const clusterSeries = clusters.map((cluster) => {
  const data = [];
  for (let i = 0; i < pointsPerCluster; i++) {
    data.push([
      cluster.center[0] + gaussian() * cluster.spread,
      cluster.center[1] + gaussian() * cluster.spread,
    ]);
  }
  return {
    type: "scatter",
    name: cluster.name,
    data,
    opacity: 0.6,
    marker: { radius: 4, symbol: cluster.symbol },
  };
});

const centroidSeries = {
  type: "scatter",
  name: "Cluster centroids",
  showInLegend: false,
  enableMouseTracking: false,
  marker: { enabled: false },
  dataLabels: {
    enabled: true,
    format: "{point.name}",
    style: {
      color: t.ink,
      fontSize: "14px",
      fontWeight: "600",
      textOutline: `3px ${t.pageBg}`,
    },
  },
  data: clusters.map((cluster) => ({
    x: cluster.center[0],
    y: cluster.center[1],
    name: cluster.name,
  })),
};

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "scatter-embedding · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "UMAP projection (n_neighbors=15) of support-ticket embeddings, colored by topic cluster",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "UMAP Dimension 1", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: { enabled: false },
    tickLength: 0,
    lineColor: t.inkSoft,
    gridLineWidth: 1,
    gridLineColor: t.grid,
  },
  yAxis: {
    title: { text: "UMAP Dimension 2", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: { enabled: false },
    tickLength: 0,
    lineColor: t.inkSoft,
    gridLineWidth: 1,
    gridLineColor: t.grid,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    pointFormat: "x: {point.x:.2f}, y: {point.y:.2f}",
  },
  plotOptions: {
    series: { animation: false },
    scatter: { states: { hover: { enabled: false } } },
  },
  series: [...clusterSeries, centroidSeries],
});
