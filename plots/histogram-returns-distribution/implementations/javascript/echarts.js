// anyplot.ai
// histogram-returns-distribution: Returns Distribution Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width: W, height: H } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const n = 252; // one trading year of daily returns
const returns = [];
for (let i = 0; i < n; i++) {
  let r = 0.0004 + 0.011 * randNormal(); // ~0.04% mean, 1.1% daily std
  if (rand() < 0.06) {
    // occasional volatility-cluster shock, skewed toward downside (crash risk)
    const sign = rand() < 0.65 ? -1 : 1;
    r += sign * (0.02 + 0.025 * rand());
  }
  returns.push(r * 100); // percent
}

// --- Statistics ---------------------------------------------------------------
const mean = returns.reduce((a, r) => a + r, 0) / n;
const variance = returns.reduce((a, r) => a + (r - mean) ** 2, 0) / n;
const std = Math.sqrt(variance);
const skewness = returns.reduce((a, r) => a + ((r - mean) / std) ** 3, 0) / n;
const kurtosis =
  returns.reduce((a, r) => a + ((r - mean) / std) ** 4, 0) / n - 3;

function normalPdf(x) {
  return (
    (1 / (std * Math.sqrt(2 * Math.PI))) *
    Math.exp(-0.5 * ((x - mean) / std) ** 2)
  );
}

// --- Histogram binning (density-normalized) ----------------------------------
const binCount = 25;
const min = Math.min(...returns);
const max = Math.max(...returns);
const binWidth = (max - min) / binCount;

const counts = new Array(binCount).fill(0);
for (const r of returns) {
  const idx = Math.min(binCount - 1, Math.floor((r - min) / binWidth));
  counts[idx]++;
}

const binCenters = counts.map((_, i) => min + (i + 0.5) * binWidth);
const densities = counts.map((c) => c / (n * binWidth));
const normalCurve = binCenters.map((x) => normalPdf(x));

const tailLo = mean - 2 * std;
const tailHi = mean + 2 * std;
const barData = binCenters.map((x, i) => ({
  value: densities[i],
  itemStyle: { color: x < tailLo || x > tailHi ? t.amber : t.palette[0] },
}));
const categories = binCenters.map((x) => `${x.toFixed(1)}%`);

// --- Title (fontsize scales with title length, 67-char baseline) ------------
const titleText =
  "Equity ETF Daily Returns · histogram-returns-distribution · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

// --- Stats box (spec explicitly requires a stats text box) ------------------
const boxW = 380;
const boxH = 220;
const boxX = W - 60 - boxW;
const boxY = 160;
const statLines = [
  `Observations: ${n}`,
  `Mean: ${mean.toFixed(3)}%`,
  `Std dev: ${std.toFixed(3)}%`,
  `Skewness: ${skewness.toFixed(2)}`,
  `Kurtosis: ${kurtosis.toFixed(2)}`,
];

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize },
  },
  legend: {
    top: 66,
    left: "center",
    data: ["Daily returns", "Normal fit"],
    itemWidth: 24,
    itemHeight: 14,
    textStyle: { color: t.inkSoft, fontSize: 15 },
  },
  tooltip: { trigger: "axis" },
  grid: { left: 100, right: 60, top: 150, bottom: 110 },
  xAxis: {
    type: "category",
    data: categories,
    name: "Daily return",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 2 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Density",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Daily returns",
      type: "bar",
      data: barData,
      barCategoryGap: "10%",
      z: 2,
    },
    {
      name: "Normal fit",
      type: "line",
      data: normalCurve,
      symbol: "none",
      smooth: true,
      lineStyle: { width: 3, color: t.palette[2] },
      z: 3,
    },
  ],
  graphic: [
    {
      type: "rect",
      left: boxX,
      top: boxY,
      shape: { width: boxW, height: boxH, r: 10 },
      style: { fill: t.elevatedBg, stroke: t.grid, lineWidth: 1 },
    },
    {
      type: "text",
      left: boxX + 24,
      top: boxY + 20,
      style: { text: "Statistics", fill: t.ink, fontSize: 17, fontWeight: "bold" },
    },
    ...statLines.map((line, i) => ({
      type: "text",
      left: boxX + 24,
      top: boxY + 54 + i * 26,
      style: { text: line, fill: t.inkSoft, fontSize: 15 },
    })),
    {
      type: "rect",
      left: boxX + 24,
      top: boxY + boxH - 30,
      shape: { width: 16, height: 16, r: 3 },
      style: { fill: t.amber },
    },
    {
      type: "text",
      left: boxX + 48,
      top: boxY + boxH - 29,
      style: { text: "Tail region (|z| > 2)", fill: t.inkSoft, fontSize: 13 },
    },
  ],
});
