// anyplot.ai
// ice-basic: Individual Conditional Expectation (ICE) Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const N_OBS = 60;
const N_GRID = 60;
const SQFT_MIN = 800;
const SQFT_MAX = 4000;

const grid = [];
for (let j = 0; j < N_GRID; j++) {
  grid.push(SQFT_MIN + (j / (N_GRID - 1)) * (SQFT_MAX - SQFT_MIN));
}

// Simulated GradientBoostingRegressor predictions: each house gets its own
// baseline value, price-per-sqft slope, and saturation curvature, producing
// heterogeneous, non-linear individual curves around a shared trend — some
// houses keep appreciating with size, others hit a price ceiling.
const curves = [];
const actualSqft = [];
for (let i = 0; i < N_OBS; i++) {
  const base = 180000 + (lcg() - 0.5) * 50000;
  const slope = 120 + lcg() * 40;
  const curvature = 0.3 + lcg() * 1.0;
  actualSqft.push(SQFT_MIN + lcg() * (SQFT_MAX - SQFT_MIN));

  const curve = grid.map((sqft) => {
    const delta = sqft - SQFT_MIN;
    return base + slope * delta * (1 - (curvature * delta) / 6000);
  });
  curves.push(curve);
}

const pdp = grid.map((_, j) => {
  let sum = 0;
  for (let i = 0; i < N_OBS; i++) sum += curves[i][j];
  return sum / N_OBS;
});

let yMin = Infinity;
let yMax = -Infinity;
for (const curve of curves) {
  for (const v of curve) {
    if (v < yMin) yMin = v;
    if (v > yMax) yMax = v;
  }
}
const yRange = yMax - yMin;
const rugY = yMin - yRange * 0.05;
const yAxisMin = yMin - yRange * 0.14;

// --- Series -------------------------------------------------------------------
const iceSeries = curves.map((curve) => ({
  name: "Individual houses (ICE)",
  type: "line",
  data: grid.map((x, j) => [x, curve[j]]),
  showSymbol: false,
  silent: true,
  lineStyle: { color: t.palette[0], width: 1.3, opacity: 0.18 },
  itemStyle: { color: t.palette[0] },
  z: 1,
}));

const pdpSeries = {
  name: "Average prediction (PDP)",
  type: "line",
  data: grid.map((x, j) => [x, pdp[j]]),
  showSymbol: false,
  lineStyle: { color: t.ink, width: 4 },
  itemStyle: { color: t.ink },
  z: 3,
};

const rugSeries = {
  name: "Observed square footage",
  type: "scatter",
  data: actualSqft.map((x) => [x, rugY]),
  symbol: "rect",
  symbolSize: [3, 16],
  itemStyle: { color: t.muted, opacity: 0.55 },
  silent: true,
  z: 2,
};

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "House Price ICE · ice-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Individual houses (ICE)", "Average prediction (PDP)"],
    top: 66,
    left: "center",
    textStyle: { color: t.ink, fontSize: 15 },
    itemWidth: 30,
    itemHeight: 14,
  },
  tooltip: {
    trigger: "item",
    formatter: (params) => {
      const [sqft, price] = params.data;
      return `${params.seriesName}<br/>${Math.round(sqft).toLocaleString()} sq ft → $${Math.round(price).toLocaleString()}`;
    },
  },
  grid: { left: 115, right: 60, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    min: SQFT_MIN,
    max: SQFT_MAX,
    name: "Square Footage (sq ft)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: yAxisMin,
    name: "Predicted Price ($)",
    nameLocation: "middle",
    nameGap: 70,
    nameRotate: 90,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: (value) => "$" + Math.round(value / 1000) + "k",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [...iceSeries, pdpSeries, rugSeries],
});
