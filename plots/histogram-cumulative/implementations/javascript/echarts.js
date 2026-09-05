// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: warehouse order processing times (minutes), deterministic LCG ----
function makeLcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

// Two processing streams: automated picking (fast) and manual picking (slower)
const processingTimes = [];
for (let i = 0; i < 420; i++) processingTimes.push(randNormal(18, 5));
for (let i = 0; i < 180; i++) processingTimes.push(randNormal(38, 9));

// --- Histogram + cumulative percentage --------------------------------------
const binCount = 20;
const minVal = Math.max(0, Math.min(...processingTimes));
const maxVal = Math.max(...processingTimes);
const binWidth = (maxVal - minVal) / binCount;

const counts = new Array(binCount).fill(0);
processingTimes.forEach((v) => {
  let idx = Math.floor((v - minVal) / binWidth);
  if (idx >= binCount) idx = binCount - 1;
  if (idx < 0) idx = 0;
  counts[idx] += 1;
});

const binEdges = [];
for (let i = 0; i <= binCount; i++) binEdges.push(minVal + i * binWidth);
const labels = binEdges.slice(1).map((edge) => edge.toFixed(0));

let running = 0;
const cumulativePct = counts.map((c) => {
  running += c;
  return Number(((running / processingTimes.length) * 100).toFixed(1));
});

// Evenly spaced round-number tick labels (every 10 minutes) instead of the
// raw, irregular bin-edge values.
const maxRounded = Math.ceil(maxVal / 10) * 10;
const tickLabelByIndex = new Map();
for (let v = 10; v <= maxRounded; v += 10) {
  const idx = Math.max(
    0,
    Math.min(binCount - 1, Math.round((v - minVal) / binWidth) - 1)
  );
  tickLabelByIndex.set(idx, String(v));
}

// Interpolate the median processing time (the 50th-percentile crossing) so
// it can be called out directly on the curve.
const half = processingTimes.length / 2;
let cumBefore = 0;
let medianBinIndex = binCount - 1;
let medianTime = maxVal;
for (let i = 0; i < binCount; i++) {
  const cumAfter = cumBefore + counts[i];
  if (cumAfter >= half) {
    medianBinIndex = i;
    const fraction = counts[i] === 0 ? 0 : (half - cumBefore) / counts[i];
    medianTime = minVal + (i + fraction) * binWidth;
    break;
  }
  cumBefore = cumAfter;
}

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "histogram-cumulative · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 110, right: 60, top: 100, bottom: 110 },
  tooltip: {
    trigger: "axis",
    valueFormatter: (value) => `${value}%`,
  },
  xAxis: {
    type: "category",
    data: labels,
    name: "Processing Time (minutes)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      interval: (index) => tickLabelByIndex.has(index),
      formatter: (value, index) => tickLabelByIndex.get(index) ?? "",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    max: 100,
    name: "Cumulative Orders (%)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13, formatter: "{value}%" },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "bar",
      name: "Cumulative Orders",
      data: cumulativePct,
      barWidth: "88%",
      itemStyle: { color: t.palette[0], borderRadius: [3, 3, 0, 0] },
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: {
          color: t.inkSoft,
          fontSize: 12,
          formatter: "50th percentile",
          position: "insideStartTop",
        },
        data: [{ yAxis: 50 }],
      },
      markPoint: {
        symbol: "circle",
        symbolSize: 14,
        itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 2 },
        label: {
          show: true,
          color: t.ink,
          fontSize: 13,
          fontWeight: 600,
          position: "top",
          distance: 12,
          formatter: `Median ≈ ${medianTime.toFixed(0)} min`,
        },
        data: [{ coord: [medianBinIndex, cumulativePct[medianBinIndex]] }],
      },
    },
  ],
});
