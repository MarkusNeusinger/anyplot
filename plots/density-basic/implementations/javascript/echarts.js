// anyplot.ai
// density-basic: Basic Density Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data: server response latency (ms), right-skewed --------------------
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

function randNormal() {
  let u = 0;
  let v = 0;
  while (u === 0) u = rand();
  while (v === 0) v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const sampleCount = 400;
const logMean = Math.log(120); // median latency ~120ms
const logStd = 0.35;
const latencies = [];
for (let i = 0; i < sampleCount; i++) {
  latencies.push(Math.exp(logMean + logStd * randNormal()));
}

// --- Gaussian KDE with Silverman's rule-of-thumb bandwidth ----------------
const mean = latencies.reduce((a, b) => a + b, 0) / sampleCount;
const variance = latencies.reduce((a, b) => a + (b - mean) ** 2, 0) / (sampleCount - 1);
const std = Math.sqrt(variance);
const bandwidth = 1.06 * std * Math.pow(sampleCount, -1 / 5);

function gaussianKernel(u) {
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
}

const vmin = Math.min(...latencies);
const vmax = Math.max(...latencies);
const pad = bandwidth * 3;
const gridStart = Math.max(0, vmin - pad);
const gridEnd = vmax + pad;
const gridCount = 200;
const step = (gridEnd - gridStart) / (gridCount - 1);

const densityCurve = [];
let peakDensity = 0;
for (let i = 0; i < gridCount; i++) {
  const x = gridStart + i * step;
  let sum = 0;
  for (let j = 0; j < sampleCount; j++) {
    sum += gaussianKernel((x - latencies[j]) / bandwidth);
  }
  const density = sum / (sampleCount * bandwidth);
  peakDensity = Math.max(peakDensity, density);
  densityCurve.push([x, density]);
}

// Rug plot: individual observations as ticks below the curve
const rugY = -peakDensity * 0.06;
const rugData = latencies.map((v) => [v, rugY]);

// Round the x-axis to clean bounds instead of the raw KDE grid extent
const xMax = Math.ceil(gridEnd / 50) * 50;

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
const title = "Server Response Latency · density-basic · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  grid: { left: 110, right: 70, top: 110, bottom: 100 },
  xAxis: {
    type: "value",
    name: "Response Latency (ms)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: xMax,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Density",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: rugY * 1.6,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => (v < 0 ? "" : v.toFixed(3)) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Density",
      type: "line",
      data: densityCurve,
      symbol: "none",
      smooth: false,
      lineStyle: { color: t.palette[0], width: 3.5 },
      areaStyle: { color: t.palette[0], opacity: 0.28 },
      z: 2,
    },
    {
      name: "Observations",
      type: "scatter",
      data: rugData,
      symbol: "rect",
      symbolSize: [1.5, 11],
      itemStyle: { color: t.inkSoft, opacity: 0.4 },
      z: 1,
    },
  ],
});
