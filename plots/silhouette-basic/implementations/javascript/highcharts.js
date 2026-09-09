// anyplot.ai
// silhouette-basic: Silhouette Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Helpers -----------------------------------------------------------------
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}

function clusterSamples(count, meanScore, spread, misclassifiedTail) {
  const scores = [];
  for (let i = 0; i < count; i++) {
    let score = meanScore + (nextRandom() - 0.5) * spread;
    if (misclassifiedTail && i >= count - Math.round(count * 0.1)) {
      score -= nextRandom() * 0.6;
    }
    scores.push(Math.max(-1, Math.min(1, score)));
  }
  scores.sort((a, b) => b - a);
  return scores;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Data (in-memory, deterministic) ------------------------------------------
// Silhouette coefficients for a k=3 clustering of an iris-like dataset. Within
// each cluster, samples are sorted descending by score — the classic layout
// popularised by sklearn.metrics.silhouette_samples plots.
const clusterDefs = [
  { name: "Cluster 0", count: 55, meanScore: 0.72, spread: 0.26, misclassifiedTail: false },
  { name: "Cluster 1", count: 50, meanScore: 0.46, spread: 0.42, misclassifiedTail: false },
  { name: "Cluster 2", count: 40, meanScore: 0.27, spread: 0.5, misclassifiedTail: true },
];

const data = [];
const categories = [];
const plotBands = [];
let allScores = [];
let cursor = 0;

clusterDefs.forEach((cluster, clusterIndex) => {
  const scores = clusterSamples(cluster.count, cluster.meanScore, cluster.spread, cluster.misclassifiedTail);
  const color = t.palette[clusterIndex];
  const startIndex = cursor;

  scores.forEach((score) => {
    data.push({ y: Math.round(score * 1000) / 1000, color });
    categories.push("");
    cursor += 1;
  });
  allScores = allScores.concat(scores);

  const clusterAvg = scores.reduce((sum, v) => sum + v, 0) / scores.length;
  plotBands.push({
    from: startIndex - 0.5,
    to: cursor - 0.5,
    color: hexToRgba(color, 0.08),
    label: {
      text: `${cluster.name} · avg ${clusterAvg.toFixed(2)}`,
      align: "right",
      x: -10,
      y: 16,
      useHTML: true,
      style: {
        color: t.inkSoft,
        fontSize: "14px",
        background: t.pageBg,
        padding: "2px 6px",
        borderRadius: "3px",
      },
    },
  });

  // Gap between clusters for visual separation
  if (clusterIndex < clusterDefs.length - 1) {
    data.push(null);
    categories.push("");
    cursor += 1;
  }
});

const overallAverage = allScores.reduce((sum, v) => sum + v, 0) / allScores.length;
const axisMin = Math.floor(Math.min(...allScores, 0) * 10) / 10 - 0.05;

// --- Chart --------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "bar",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "silhouette-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Iris-like dataset · k-means, k = 3 · samples sorted by silhouette score within cluster",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories,
    labels: { enabled: false },
    lineColor: t.inkSoft,
    tickLength: 0,
    title: { text: "Samples (grouped by cluster)", style: { color: t.inkSoft, fontSize: "16px" } },
    plotBands,
  },
  yAxis: {
    min: axisMin,
    max: 1,
    tickInterval: 0.2,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    title: { text: "Silhouette coefficient", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: 0,
        color: t.grid,
        width: 1,
        zIndex: 4,
      },
      {
        value: overallAverage,
        color: t.ink,
        dashStyle: "Dash",
        width: 2,
        zIndex: 5,
        label: {
          text: `Overall avg ${overallAverage.toFixed(2)}`,
          align: "center",
          verticalAlign: "top",
          y: 28,
          useHTML: true,
          style: {
            color: t.ink,
            fontSize: "14px",
            fontWeight: "600",
            background: t.pageBg,
            padding: "2px 6px",
            borderRadius: "3px",
          },
        },
      },
    ],
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false, pointPadding: 0.05, groupPadding: 0 },
    bar: { borderWidth: 0 },
  },
  tooltip: {
    pointFormat: "Silhouette score: <b>{point.y:.2f}</b>",
  },
  series: [
    {
      name: "Silhouette score",
      data,
    },
  ],
});
