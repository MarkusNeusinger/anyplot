// anyplot.ai
// swarm-basic: Basic Swarm Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-07-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// CRP (C-reactive protein) biomarker levels across a dose-escalation trial.
function lcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = lcg(42);
function randNormal() {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const groups = [
  { name: "Placebo", n: 45, mean: 3.2, sd: 0.9 },
  { name: "Low Dose", n: 45, mean: 2.6, sd: 0.8 },
  { name: "Medium Dose", n: 45, mean: 1.9, sd: 0.7 },
  { name: "High Dose", n: 45, mean: 1.3, sd: 0.6 },
];
const categories = groups.map((g) => g.name);
const groupValues = groups.map((g) =>
  Array.from({ length: g.n }, () => Math.max(0.1, g.mean + randNormal() * g.sd)),
);

// --- Beeswarm layout ---------------------------------------------------------
// ECharts has no native swarm/beeswarm series, so points are bucketed into
// fine value bins per category and stacked symmetrically outward within each
// bin — the classic histogram-based beeswarm construction.
function beeswarmOffsets(values) {
  const n = values.length;
  const order = values.map((_, i) => i).sort((a, b) => values[a] - values[b]);
  const sorted = order.map((i) => values[i]);
  const range = sorted[n - 1] - sorted[0] || 1;
  const binCount = Math.max(10, Math.round(Math.sqrt(n) * 3));
  const binWidth = range / binCount;
  const bins = new Map();
  sorted.forEach((v, sortedIdx) => {
    const b = Math.min(binCount - 1, Math.floor((v - sorted[0]) / binWidth));
    if (!bins.has(b)) bins.set(b, []);
    bins.get(b).push(sortedIdx);
  });
  const spacing = 0.075;
  const maxOffset = 0.42;
  const offsetsBySortedIdx = new Array(n);
  for (const members of bins.values()) {
    members.forEach((sortedIdx, k) => {
      const side = k % 2 === 0 ? 1 : -1;
      const step = Math.ceil((k + 1) / 2);
      offsetsBySortedIdx[sortedIdx] = Math.max(-maxOffset, Math.min(maxOffset, side * step * spacing));
    });
  }
  const offsets = new Array(n);
  order.forEach((origIdx, sortedIdx) => {
    offsets[origIdx] = offsetsBySortedIdx[sortedIdx];
  });
  return offsets;
}

const pointSeries = groups.map((g, ci) => {
  const values = groupValues[ci];
  const offsets = beeswarmOffsets(values);
  return {
    name: g.name,
    type: "scatter",
    data: values.map((v, i) => [ci + offsets[i], v]),
    symbolSize: 14,
    itemStyle: { color: t.palette[ci], opacity: 0.8 },
  };
});

const meanSeries = {
  name: "Group mean",
  type: "scatter",
  data: groups.map((g, ci) => [ci, g.mean]),
  symbol: "diamond",
  symbolSize: 24,
  itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 2 },
  z: 3,
};

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "swarm-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 100, right: 60, top: 100, bottom: 80 },
  tooltip: {
    trigger: "item",
    formatter: (p) => `${categories[Math.round(p.value[0])] ?? p.seriesName}<br/>CRP: ${p.value[1].toFixed(2)} mg/L`,
  },
  xAxis: {
    type: "value",
    min: 0,
    max: categories.length - 1,
    interval: 1,
    boundaryGap: ["12%", "12%"],
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => categories[v] ?? "" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "CRP (mg/L)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [...pointSeries, meanSeries],
});
