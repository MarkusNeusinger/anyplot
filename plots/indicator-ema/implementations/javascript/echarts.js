// anyplot.ai
// indicator-ema: Exponential Moving Average (EMA) Indicator Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simple LCG so the sample data is reproducible without Math.random().
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const PERIODS = 120;
const SHORT_PERIOD = 12;
const LONG_PERIOD = 26;

const startDate = new Date(Date.UTC(2026, 0, 5));
const dates = [];
for (let i = 0; i < PERIODS; i++) {
  const dt = new Date(startDate.getTime() + i * 86400000);
  dates.push(
    `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, "0")}-${String(dt.getUTCDate()).padStart(2, "0")}`,
  );
}

// Daily close price: a random walk with three drift regimes — an opening
// pullback, then a rally, then a second pullback — so the EMA lines produce
// both a golden cross (bullish) and a death cross (bearish) naturally rather
// than by construction.
const close = [148.5];
for (let i = 1; i < PERIODS; i++) {
  let drift;
  if (i < PERIODS * 0.3) drift = -0.4;
  else if (i < PERIODS * 0.7) drift = 0.45;
  else drift = -0.35;
  const noise = (rand() - 0.5) * 3.2;
  close.push(Math.max(close[i - 1] + drift + noise, 5));
}

function ema(values, period) {
  const k = 2 / (period + 1);
  const out = new Array(values.length).fill(null);
  const seedAvg = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  out[period - 1] = seedAvg;
  for (let i = period; i < values.length; i++) {
    out[i] = values[i] * k + out[i - 1] * (1 - k);
  }
  return out;
}

const emaShort = ema(close, SHORT_PERIOD);
const emaLong = ema(close, LONG_PERIOD);

// Crossover points: short EMA moving from below to above the long EMA is a
// golden cross (bullish); above to below is a death cross (bearish).
const goldenCrosses = [];
const deathCrosses = [];
for (let i = LONG_PERIOD; i < PERIODS; i++) {
  const prevDiff = emaShort[i - 1] - emaLong[i - 1];
  const diff = emaShort[i] - emaLong[i];
  if (prevDiff <= 0 && diff > 0) goldenCrosses.push({ coord: [dates[i], emaShort[i]], name: "Golden Cross" });
  if (prevDiff >= 0 && diff < 0) deathCrosses.push({ coord: [dates[i], emaShort[i]], name: "Death Cross" });
}

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: t.palette,
  title: {
    text: "indicator-ema · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "cross" },
    valueFormatter: (value) => `$${Number(value).toFixed(2)}`,
  },
  legend: {
    data: ["Close", `EMA (${SHORT_PERIOD})`, `EMA (${LONG_PERIOD})`],
    top: 66,
    left: "center",
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 22,
    itemHeight: 12,
  },
  grid: {
    left: 90,
    right: 60,
    top: 130,
    bottom: 90,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    data: dates,
    boundaryGap: false,
    name: "Date",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      rotate: 45,
      interval: (index) => index % 10 === 0,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    scale: true,
    name: "Price (USD)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 13, formatter: (v) => `$${v}` },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Close",
      type: "line",
      data: close,
      symbol: "none",
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      z: 3,
    },
    {
      name: `EMA (${SHORT_PERIOD})`,
      type: "line",
      data: emaShort,
      symbol: "none",
      lineStyle: { width: 1.75, color: t.palette[2] },
      itemStyle: { color: t.palette[2] },
      z: 2,
      markPoint: {
        symbolSize: 40,
        label: { show: false },
        data: [
          ...goldenCrosses.map((p) => ({ ...p, symbol: "triangle", itemStyle: { color: t.palette[7] } })),
          ...deathCrosses.map((p) => ({ ...p, symbol: "triangle", symbolRotate: 180, itemStyle: { color: t.palette[4] } })),
        ],
      },
    },
    {
      name: `EMA (${LONG_PERIOD})`,
      type: "line",
      data: emaLong,
      symbol: "none",
      lineStyle: { width: 1.75, color: t.palette[3] },
      itemStyle: { color: t.palette[3] },
      z: 2,
    },
  ],
});
