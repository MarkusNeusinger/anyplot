// anyplot.ai
// histogram-density: Density Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Reaction times (ms) from a simulated cognitive-task experiment, n=600.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

function randomNormal() {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const sampleCount = 600;
const trueMean = 620;
const trueStd = 85;
const reactionTimes = Array.from(
  { length: sampleCount },
  () => trueMean + trueStd * randomNormal(),
);

// Sample statistics feed the theoretical PDF overlay (goodness-of-fit check).
const sampleMean = reactionTimes.reduce((a, b) => a + b, 0) / sampleCount;
const variance =
  reactionTimes.reduce((a, b) => a + (b - sampleMean) ** 2, 0) / sampleCount;
const sampleStd = Math.sqrt(variance);

// --- Binning: normalize so total bar area == 1 (density, not raw count) ----
const binCount = 26;
const minValue = Math.min(...reactionTimes);
const maxValue = Math.max(...reactionTimes);
const binWidth = (maxValue - minValue) / binCount;
const counts = new Array(binCount).fill(0);
reactionTimes.forEach((value) => {
  const idx = Math.min(binCount - 1, Math.floor((value - minValue) / binWidth));
  counts[idx] += 1;
});

const binCenters = counts.map((_, i) => minValue + (i + 0.5) * binWidth);
const binLabels = binCenters.map((c) => Math.round(c).toString());
const densities = counts.map((count) => count / (sampleCount * binWidth));

// Theoretical normal PDF fit to the sample, evaluated at the same bin centers.
const normalPdf = binCenters.map((x) => {
  const z = (x - sampleMean) / sampleStd;
  return Math.exp(-0.5 * z * z) / (sampleStd * Math.sqrt(2 * Math.PI));
});

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "histogram-density · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Observed density", "Normal fit"],
    top: 62,
    textStyle: { color: t.inkSoft, fontSize: 15 },
  },
  grid: { left: 100, right: 60, top: 120, bottom: 90 },
  xAxis: {
    type: "category",
    data: binLabels,
    name: "Reaction Time (ms)",
    nameLocation: "center",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Density",
    nameLocation: "center",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (value) => value.toFixed(3) },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Observed density",
      type: "bar",
      data: densities,
      barCategoryGap: "0%",
      itemStyle: { color: t.palette[0] },
      z: 2,
    },
    {
      name: "Normal fit",
      type: "line",
      data: normalPdf,
      smooth: true,
      symbol: "none",
      lineStyle: { color: t.ink, width: 3, type: "dashed" },
      z: 3,
    },
  ],
});
