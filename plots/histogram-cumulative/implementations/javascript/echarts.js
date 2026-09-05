// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05

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
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 1 },
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
    },
  ],
});
