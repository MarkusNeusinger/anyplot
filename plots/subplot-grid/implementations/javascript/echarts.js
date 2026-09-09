// anyplot.ai
// subplot-grid: Subplot Grid Layout
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Mulberry32 PRNG — the browser has no seeded Math.random(), so a tiny
// fixed-seed generator stands in for np.random.seed(42) / set.seed(42).
function mulberry32(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

const DAYS = 60;
const startDate = new Date(Date.UTC(2024, 0, 2));
const dates = [];
const closePrices = [];
const dailyVolumes = [];
const dailyReturns = [];

let price = 150;
for (let i = 0; i < DAYS; i++) {
  const d = new Date(startDate);
  d.setUTCDate(d.getUTCDate() + i);
  dates.push(`${d.getUTCMonth() + 1}/${d.getUTCDate()}`);

  const changePct = (rand() - 0.5) * 4; // daily move in [-2%, +2%]
  price *= 1 + changePct / 100;
  closePrices.push(Math.round(price * 100) / 100);
  dailyReturns.push(Math.round(changePct * 100) / 100);

  const baseVolume = 500000 + rand() * 1500000;
  const spike = Math.abs(changePct) * 400000; // big moves trade heavier volume
  dailyVolumes.push(Math.round(baseVolume + spike));
}

// Histogram of daily returns — 10 equal-width bins.
const BIN_COUNT = 10;
const minReturn = Math.min(...dailyReturns);
const maxReturn = Math.max(...dailyReturns);
const binWidth = (maxReturn - minReturn) / BIN_COUNT;
const binLabels = [];
const binCounts = new Array(BIN_COUNT).fill(0);
for (let i = 0; i < BIN_COUNT; i++) {
  binLabels.push((minReturn + i * binWidth).toFixed(1));
}
dailyReturns.forEach((r) => {
  let idx = Math.floor((r - minReturn) / binWidth);
  if (idx >= BIN_COUNT) idx = BIN_COUNT - 1;
  if (idx < 0) idx = 0;
  binCounts[idx]++;
});
const binData = binCounts.map((count, i) => ({
  value: count,
  // Semantic exception: up/gain -> green, down/loss -> red (finance convention).
  itemStyle: { color: Number(binLabels[i]) >= 0 ? t.palette[0] : t.palette[4] },
}));

// Volume-vs-return scatter (bottom-right cell) — volume in millions.
const returnVsVolume = dailyReturns.map((r, i) => [dailyVolumes[i] / 1e6, r]);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
// Layout: 2x2 grid — each cell a distinct plot type against the same trading
// window. Top row shares the date axis geometry (price vs. volume, same
// x-domain and width) for direct visual comparison; bottom row uses
// independent axes since the histogram (return bins) and scatter (volume)
// plot unrelated domains.
const COLUMN = { left: "6%", width: "41%" };
const COLUMN_RIGHT = { left: "55%", width: "41%" };
const ROW_TOP = { top: "17%", height: "32%" };
const ROW_BOTTOM = { top: "62%", height: "32%" };

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  textStyle: { color: t.inkSoft },
  tooltip: { trigger: "axis" },
  title: [
    {
      text: "subplot-grid · javascript · echarts · anyplot.ai",
      left: "center",
      top: "2%",
      textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
    },
    { text: "Closing Price ($)", left: COLUMN.left, top: "12%", textStyle: { color: t.ink, fontSize: 16, fontWeight: "normal" } },
    { text: "Daily Volume", left: COLUMN_RIGHT.left, top: "12%", textStyle: { color: t.ink, fontSize: 16, fontWeight: "normal" } },
    { text: "Daily Returns Distribution", left: COLUMN.left, top: "57%", textStyle: { color: t.ink, fontSize: 16, fontWeight: "normal" } },
    { text: "Volume vs. Return", left: COLUMN_RIGHT.left, top: "57%", textStyle: { color: t.ink, fontSize: 16, fontWeight: "normal" } },
  ],
  grid: [
    { ...COLUMN, ...ROW_TOP, containLabel: true }, // 0: price line
    { ...COLUMN_RIGHT, ...ROW_TOP, containLabel: true }, // 1: volume bar
    { ...COLUMN, ...ROW_BOTTOM, containLabel: true }, // 2: returns histogram
    { ...COLUMN_RIGHT, ...ROW_BOTTOM, containLabel: true }, // 3: volume-vs-return scatter
  ],
  xAxis: [
    {
      gridIndex: 0,
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLabel: { color: t.inkSoft, fontSize: 12, interval: 9 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { show: false },
    },
    {
      gridIndex: 1,
      type: "category",
      data: dates,
      axisLabel: { color: t.inkSoft, fontSize: 12, interval: 9 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { show: false },
    },
    {
      gridIndex: 2,
      type: "category",
      data: binLabels,
      name: "Daily return (%)",
      nameLocation: "middle",
      nameGap: 32,
      nameTextStyle: { color: t.inkSoft, fontSize: 13 },
      axisLabel: { color: t.inkSoft, fontSize: 12, rotate: 45 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { show: false },
    },
    {
      gridIndex: 3,
      type: "value",
      name: "Volume (M)",
      nameLocation: "middle",
      nameGap: 32,
      nameTextStyle: { color: t.inkSoft, fontSize: 13 },
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
  ],
  yAxis: [
    {
      gridIndex: 0,
      type: "value",
      scale: true,
      axisLabel: { color: t.inkSoft, fontSize: 12, formatter: "${value}" },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      gridIndex: 1,
      type: "value",
      axisLabel: { color: t.inkSoft, fontSize: 12, formatter: (v) => `${(v / 1e6).toFixed(1)}M` },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      gridIndex: 2,
      type: "value",
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      gridIndex: 3,
      type: "value",
      axisLabel: { color: t.inkSoft, fontSize: 12, formatter: "{value}%" },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
  ],
  series: [
    {
      name: "Close price",
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: closePrices,
      showSymbol: false,
      lineStyle: { width: 3, color: t.palette[0] },
      areaStyle: { color: t.palette[0], opacity: 0.08 },
    },
    {
      name: "Volume",
      type: "bar",
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: dailyVolumes,
      itemStyle: { color: t.palette[2] },
      barMaxWidth: 10,
    },
    {
      name: "Return frequency",
      type: "bar",
      xAxisIndex: 2,
      yAxisIndex: 2,
      data: binData,
      barMaxWidth: 34,
    },
    {
      name: "Volume vs. return",
      type: "scatter",
      xAxisIndex: 3,
      yAxisIndex: 3,
      data: returnVsVolume,
      symbolSize: 12,
      itemStyle: { color: t.palette[5], opacity: 0.8 },
    },
  ],
});
