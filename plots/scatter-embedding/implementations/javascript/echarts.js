// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + Box-Muller for gaussian jitter --------------
let seed = 20260811;
function rnd() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gauss() {
  const u1 = Math.max(rnd(), 1e-9);
  const u2 = rnd();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Synthetic single-cell RNA-seq UMAP embedding ---------------------------
// 8 cell-type clusters, each with its own center, elongation and rotation —
// mimics a real UMAP projection where cluster shape/density varies by type,
// rather than uniform circular blobs.
const CLUSTERS = [
  { label: "T cells", cx: -6.5, cy: 3.0, sx: 1.3, sy: 1.0, rot: 0.4, n: 95 },
  { label: "B cells", cx: -3.0, cy: 6.0, sx: 1.0, sy: 0.9, rot: -0.3, n: 70 },
  { label: "NK cells", cx: -8.0, cy: -1.0, sx: 0.9, sy: 1.1, rot: 0.8, n: 55 },
  { label: "Monocytes", cx: 4.0, cy: 4.5, sx: 1.6, sy: 1.3, rot: 0.2, n: 90 },
  { label: "Dendritic cells", cx: 6.5, cy: 1.0, sx: 0.8, sy: 0.8, rot: 0.0, n: 40 },
  { label: "Neutrophils", cx: 2.0, cy: -4.5, sx: 1.4, sy: 1.0, rot: -0.5, n: 65 },
  { label: "Erythrocytes", cx: -1.5, cy: -7.0, sx: 1.1, sy: 1.4, rot: 0.6, n: 80 },
  { label: "Platelets", cx: 7.5, cy: -6.0, sx: 0.7, sy: 0.7, rot: 0.0, n: 35 },
];

const clusterSeries = CLUSTERS.map((c) => {
  const points = [];
  for (let i = 0; i < c.n; i++) {
    const gx = gauss() * c.sx;
    const gy = gauss() * c.sy;
    const rx = gx * Math.cos(c.rot) - gy * Math.sin(c.rot);
    const ry = gx * Math.sin(c.rot) + gy * Math.cos(c.rot);
    points.push([c.cx + rx, c.cy + ry]);
  }
  return {
    name: c.label,
    type: "scatter",
    data: points,
    symbolSize: 11,
    itemStyle: { opacity: 0.65, borderColor: t.pageBg, borderWidth: 0.5 },
    emphasis: { itemStyle: { opacity: 1, borderWidth: 1.5 } },
  };
});

const centroidLabels = {
  name: "centroids",
  type: "scatter",
  silent: true,
  symbolSize: 0,
  data: CLUSTERS.map((c) => ({ value: [c.cx, c.cy], name: c.label })),
  label: {
    show: true,
    formatter: "{b}",
    color: t.ink,
    fontSize: 15,
    fontWeight: 600,
    textShadowColor: t.pageBg,
    textShadowBlur: 6,
  },
};

// --- Render -------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "scatter-embedding · javascript · echarts · anyplot.ai",
    subtext: "UMAP (n_neighbors=15, min_dist=0.1) · colored by cell type",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 600 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  legend: {
    data: CLUSTERS.map((c) => c.label),
    orient: "vertical",
    right: 24,
    top: "middle",
    itemWidth: 14,
    itemHeight: 14,
    itemGap: 16,
    textStyle: { color: t.ink, fontSize: 15 },
  },
  tooltip: {
    trigger: "item",
    formatter: (p) => p.seriesName,
  },
  grid: { left: 60, right: 240, top: 110, bottom: 70 },
  xAxis: {
    type: "value",
    name: "UMAP dimension 1",
    nameLocation: "middle",
    nameGap: 28,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { show: false },
    axisTick: { show: false },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "UMAP dimension 2",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { show: false },
    axisTick: { show: false },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  series: [...clusterSeries, centroidLabels],
});

chart.on("finished", () => {
  window.__anyplotReady = true;
});
