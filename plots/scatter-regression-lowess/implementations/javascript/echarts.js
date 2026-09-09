// anyplot.ai
// scatter-regression-lowess: Scatter Plot with LOWESS Regression
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Enzyme reaction rate vs. temperature: rate climbs as the enzyme warms toward
// its optimum, then collapses past ~38 C as the protein denatures — a
// non-monotonic curve no single polynomial captures cleanly, which is exactly
// what LOWESS is good at tracing.
let seed = 20260909;
function rand() {
  // Small fixed-seed LCG — Math.random() is not reproducible across runs.
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const n = 160;
const optimum = 38;
const width = 7;
const peak = 95;
const temperatures = [];
const reactionRates = [];
for (let i = 0; i < n; i++) {
  const temp = 5 + rand() * 45;
  const gaussian = peak * Math.exp(-((temp - optimum) ** 2) / (2 * width * width));
  const denatureDrop = temp > optimum ? (temp - optimum) * 1.4 : 0;
  const rate = Math.max(2, gaussian - denatureDrop + randNormal() * 6);
  temperatures.push(temp);
  reactionRates.push(rate);
}

// --- LOWESS (locally weighted linear regression, single pass) --------------
const order = temperatures
  .map((temp, i) => i)
  .sort((a, b) => temperatures[a] - temperatures[b]);
const xSorted = order.map((i) => temperatures[i]);
const ySorted = order.map((i) => reactionRates[i]);

const frac = 0.35;
const windowSize = Math.max(4, Math.round(frac * n));

function tricube(u) {
  return u < 1 ? (1 - u ** 3) ** 3 : 0;
}

const lowessCurve = xSorted.map((x0, i) => {
  const distances = xSorted.map((xj) => Math.abs(xj - x0));
  const bandwidth = [...distances].sort((a, b) => a - b)[windowSize - 1] || 1e-6;

  let s0 = 0, s1 = 0, s2 = 0, sy = 0, sxy = 0;
  for (let j = 0; j < n; j++) {
    const w = tricube(distances[j] / bandwidth);
    if (w <= 0) continue;
    const xj = xSorted[j], yj = ySorted[j];
    s0 += w;
    s1 += w * xj;
    s2 += w * xj * xj;
    sy += w * yj;
    sxy += w * xj * yj;
  }
  const denom = s0 * s2 - s1 * s1;
  const slope = denom !== 0 ? (s0 * sxy - s1 * sy) / denom : 0;
  const intercept = (sy - slope * s1) / s0;
  return [x0, intercept + slope * x0];
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
const title = "scatter-regression-lowess · javascript · echarts · anyplot.ai";
const titleFontSize = title.length > 67 ? Math.max(16, Math.round(22 * (67 / title.length))) : 22;

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 100, bottom: 90 },
  legend: {
    data: ["Reaction rate", "LOWESS fit"],
    top: 50,
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },
  xAxis: {
    type: "value",
    name: "Temperature (°C)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: 55,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Reaction Rate (µmol/min)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Reaction rate",
      type: "scatter",
      data: temperatures.map((temp, i) => [temp, reactionRates[i]]),
      symbolSize: 16,
      itemStyle: { color: t.palette[0], opacity: 0.6 },
    },
    {
      name: "LOWESS fit",
      type: "line",
      data: lowessCurve,
      showSymbol: false,
      smooth: false,
      lineStyle: { color: t.palette[2], width: 5 },
      z: 10,
    },
  ],
});
