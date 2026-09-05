//# anyplot-orientation: square
// anyplot.ai
// histogram-2d: 2D Histogram Heatmap
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: deterministic bivariate-normal sample (LCG-seeded) --------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1103515245 * state + 12345) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal() {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const SAMPLE_SIZE = 6000;
const CORRELATION = 0.55;
const customerAges = [];
const purchaseFrequencies = [];
for (let i = 0; i < SAMPLE_SIZE; i++) {
  const z1 = randNormal();
  const z2 = randNormal();
  const zCorrelated = CORRELATION * z1 + Math.sqrt(1 - CORRELATION * CORRELATION) * z2;
  const age = 42 + z1 * 13;
  const frequency = 8 + zCorrelated * 3;
  if (age >= 18 && age <= 75 && frequency >= 0) {
    customerAges.push(age);
    purchaseFrequencies.push(frequency);
  }
}

// --- Binning: build the 2D histogram grid -----------------------------------
const BIN_COUNT = 28;
const xMin = Math.min(...customerAges);
const xMax = Math.max(...customerAges);
const yMin = Math.min(...purchaseFrequencies);
const yMax = Math.max(...purchaseFrequencies);
const xStep = (xMax - xMin) / BIN_COUNT;
const yStep = (yMax - yMin) / BIN_COUNT;

const binCounts = Array.from({ length: BIN_COUNT }, () => new Array(BIN_COUNT).fill(0));
for (let i = 0; i < customerAges.length; i++) {
  const xi = Math.min(BIN_COUNT - 1, Math.floor((customerAges[i] - xMin) / xStep));
  const yi = Math.min(BIN_COUNT - 1, Math.floor((purchaseFrequencies[i] - yMin) / yStep));
  binCounts[yi][xi] += 1;
}

const xLabels = Array.from({ length: BIN_COUNT }, (_, i) => (xMin + (i + 0.5) * xStep).toFixed(0));
const yLabels = Array.from({ length: BIN_COUNT }, (_, i) => (yMin + (i + 0.5) * yStep).toFixed(1));

const heatmapData = [];
let maxCount = 0;
for (let yi = 0; yi < BIN_COUNT; yi++) {
  for (let xi = 0; xi < BIN_COUNT; xi++) {
    const count = binCounts[yi][xi];
    if (count > 0) {
      heatmapData.push([xi, yi, count]);
      maxCount = Math.max(maxCount, count);
    }
  }
}

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "histogram-2d · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 120, right: 100, top: 110, bottom: 120 },
  xAxis: {
    type: "category",
    data: xLabels,
    name: "Customer Age (years)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 3 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  yAxis: {
    type: "category",
    data: yLabels,
    name: "Purchases per Year",
    nameLocation: "middle",
    nameGap: 75,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 3 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  visualMap: {
    type: "continuous",
    min: 0,
    max: maxCount,
    calculable: true,
    orient: "vertical",
    right: 10,
    top: "middle",
    text: ["Point count", ""],
    textStyle: { color: t.inkSoft, fontSize: 14 },
    inRange: { color: t.seq },
  },
  series: [
    {
      type: "heatmap",
      data: heatmapData,
      itemStyle: { borderWidth: 0 },
      emphasis: { itemStyle: { shadowBlur: 0 } },
    },
  ],
});
