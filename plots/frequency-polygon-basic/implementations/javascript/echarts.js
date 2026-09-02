// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: reaction times (ms) across three experimental conditions --------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function normalSamples(rand, mean, std, n) {
  const samples = [];
  for (let i = 0; i < n; i++) {
    const u1 = rand();
    const u2 = rand();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    samples.push(mean + z * std);
  }
  return samples;
}

const rand = lcg(42);
const groups = [
  { name: "Placebo", values: normalSamples(rand, 450, 60, 300) },
  { name: "Caffeine", values: normalSamples(rand, 400, 50, 300) },
  { name: "Sleep-deprived", values: normalSamples(rand, 520, 80, 300) },
];

// Shared bin edges across all groups so the polygons compare fairly.
const allValues = groups.flatMap((g) => g.values);
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const binCount = 18;
const binWidth = (dataMax - dataMin) / binCount;
const midpoints = Array.from({ length: binCount }, (_, i) => dataMin + (i + 0.5) * binWidth);

function toPolygon(values) {
  const counts = new Array(binCount).fill(0);
  values.forEach((v) => {
    const idx = Math.min(binCount - 1, Math.floor((v - dataMin) / binWidth));
    counts[idx] += 1;
  });
  // Extend to zero at both ends so the polygon closes.
  const points = counts.map((c, i) => [midpoints[i], c]);
  const peakIdx = counts.indexOf(Math.max(...counts));
  const peak = [midpoints[peakIdx], counts[peakIdx]];
  points.unshift([midpoints[0] - binWidth, 0]);
  points.push([midpoints[midpoints.length - 1] + binWidth, 0]);
  return { points, peak };
}

const lineStyles = ["solid", "dashed", "dotted"];
const polygons = groups.map((g) => toPolygon(g.values));

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -------------------------------------------------------------------
const title = "frequency-polygon-basic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    data: groups.map((g) => g.name),
    top: 76,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 28,
    itemHeight: 3,
  },
  tooltip: {
    trigger: "axis",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink },
    formatter: (params) =>
      [
        `${Math.round(params[0].value[0])} ms`,
        ...params.map((p) => `${p.marker} ${p.seriesName}: ${p.value[1]}`),
      ].join("<br/>"),
  },
  grid: { left: 100, right: 60, top: 150, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Reaction Time (ms)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Frequency (count)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.grid, width: 1 } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: groups.map((g, i) => ({
    name: g.name,
    type: "line",
    data: polygons[i].points,
    symbol: "circle",
    symbolSize: 7,
    lineStyle: { width: 3, type: lineStyles[i], color: t.palette[i] },
    itemStyle: { color: t.palette[i] },
    areaStyle: { color: t.palette[i], opacity: 0.12 },
    emphasis: { focus: "series", lineStyle: { width: 4 } },
    markPoint: {
      symbol: "pin",
      symbolSize: 34,
      itemStyle: { color: t.palette[i], borderColor: t.pageBg, borderWidth: 2 },
      label: {
        color: t.ink,
        fontSize: 13,
        fontWeight: 600,
        position: "top",
        distance: 6,
        formatter: () => `${Math.round(polygons[i].peak[0])} ms`,
      },
      data: [{ coord: polygons[i].peak }],
    },
  })),
});
