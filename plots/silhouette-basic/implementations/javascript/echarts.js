// anyplot.ai
// silhouette-basic: Silhouette Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-09
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gaussian(mean, std) {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Simulated silhouette coefficients for a 3-cluster k-means result on a
// flower-measurement dataset (analogous to clustering the iris species).
const clusterSpecs = [
  { name: "Cluster 0 (setosa-like)", n: 50, mean: 0.78, std: 0.08 },
  { name: "Cluster 1 (versicolor-like)", n: 62, mean: 0.42, std: 0.22 },
  { name: "Cluster 2 (virginica-like)", n: 58, mean: 0.5, std: 0.25 },
];

const clusters = clusterSpecs.map((spec) => {
  const values = [];
  for (let i = 0; i < spec.n; i++) {
    let v = gaussian(spec.mean, spec.std);
    v = Math.max(-0.35, Math.min(0.98, v));
    values.push(v);
  }
  values.sort((a, b) => a - b);
  return { name: spec.name, values };
});

let allValues = [];
clusters.forEach((c) => (allValues = allValues.concat(c.values)));
const avgSilhouette = allValues.reduce((a, b) => a + b, 0) / allValues.length;

// One horizontal bar per sample, samples stacked cluster-by-cluster with a
// thin gap between clusters (mirrors sklearn's silhouette_plot convention).
const categories = [];
const barValues = [];
const barColors = [];
const clusterAverages = [];
const gap = 3;
let cursor = 0;

clusters.forEach((cluster, ci) => {
  const clusterStart = cursor;
  cluster.values.forEach((v) => {
    categories.push("");
    barValues.push(v);
    barColors.push(t.palette[ci]);
    cursor++;
  });
  const clusterEnd = cursor;
  const clusterAvg = cluster.values.reduce((a, b) => a + b, 0) / cluster.values.length;
  clusterAverages.push({ name: cluster.name, mid: (clusterStart + clusterEnd - 1) / 2, avg: clusterAvg });
  for (let g = 0; g < gap; g++) {
    categories.push("");
    barValues.push(0);
    barColors.push("transparent");
    cursor++;
  }
});

const barData = barValues.map((v, i) => ({ value: v, itemStyle: { color: barColors[i] } }));

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "silhouette-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 190, right: 60, top: 90, bottom: 70 },
  xAxis: {
    type: "value",
    name: "Silhouette coefficient",
    nameLocation: "middle",
    nameGap: 36,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -0.4,
    max: 1,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: categories,
    inverse: true,
    axisLabel: { show: false },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "bar",
      data: barData,
      barCategoryGap: "0%",
      markLine: {
        symbol: "none",
        silent: true,
        label: { show: false },
        lineStyle: { color: t.ink, type: "dashed", width: 2 },
        data: [{ xAxis: avgSilhouette }],
      },
    },
  ],
  graphic: clusterAverages
    .map((c) => ({
      type: "text",
      left: 20,
      top: 90 + (c.mid / cursor) * (900 - 90 - 70) - 12,
      style: {
        text: `${c.name}\navg ${c.avg.toFixed(2)}`,
        fill: t.inkSoft,
        fontSize: 14,
        lineHeight: 18,
      },
    }))
    .concat([
      {
        type: "text",
        left: 190 + ((avgSilhouette + 0.4) / 1.4) * (1600 - 190 - 60) + 8,
        top: 68,
        style: {
          text: `avg = ${avgSilhouette.toFixed(2)}`,
          fill: t.ink,
          fontSize: 14,
        },
      },
    ]),
});
