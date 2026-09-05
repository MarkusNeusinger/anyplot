// anyplot.ai
// histogram-stepwise: Step Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) -----------------------------------
// Reaction times (ms) from a simulated cognitive test, n=1500.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

function randNormal(mean, std) {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const reactionTimes = [];
for (let i = 0; i < 1500; i++) {
  reactionTimes.push(randNormal(320, 55));
}

// --- Binning ----------------------------------------------------------------
const binCount = 30;
const minVal = Math.min(...reactionTimes);
const maxVal = Math.max(...reactionTimes);
const binWidth = (maxVal - minVal) / binCount;

const counts = new Array(binCount).fill(0);
for (const v of reactionTimes) {
  let idx = Math.floor((v - minVal) / binWidth);
  if (idx >= binCount) idx = binCount - 1;
  counts[idx]++;
}

// Step-line points: each bin drawn as a horizontal segment at its edges,
// closed to zero at both ends so the outline reads as a step function.
const stepData = [[minVal, 0]];
for (let i = 0; i < binCount; i++) {
  const left = minVal + i * binWidth;
  const right = left + binWidth;
  stepData.push([left, counts[i]]);
  stepData.push([right, counts[i]]);
}
stepData.push([maxVal, 0]);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "histogram-stepwise · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 90, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Reaction Time (ms)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: Math.floor(minVal / 10) * 10,
    max: Math.ceil(maxVal / 10) * 10,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Count",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: stepData,
      showSymbol: false,
      lineStyle: { color: t.palette[0], width: 3 },
      areaStyle: undefined,
      emphasis: { disabled: true },
    },
  ],
});
