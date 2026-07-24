// anyplot.ai
// qq-basic: Basic Q-Q Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reaction-time trial data (ms), right-skewed like typical human reaction
// times, compared against a standard normal reference distribution.
function makeLcg(seed) {
  let state = seed;
  return function lcg() {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

function standardNormal(rand) {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Rational approximation of the inverse standard normal CDF (Acklam's algorithm).
function invNormCdf(p) {
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
             1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
             6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838e0,
             -2.549732539343734e0, 4.374664141464968e0, 2.938163982698783e0];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0,
             3.754408661907416e0];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  if (p < pLow) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
           ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= pHigh) {
    const q = p - 0.5;
    const r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  const q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
          ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

const rand = makeLcg(42);
const n = 120;
const baseMs = 230;
const skewSigma = 0.28;
const reactionTimes = [];
for (let i = 0; i < n; i++) {
  const z = standardNormal(rand);
  reactionTimes.push(baseMs * Math.exp(skewSigma * z));
}
reactionTimes.sort((a, b) => a - b);

const mean = reactionTimes.reduce((s, v) => s + v, 0) / n;
const variance = reactionTimes.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);
const standardizedSample = reactionTimes.map((v) => (v - mean) / std);

// Blom's plotting positions matched to sorted standardized sample quantiles.
const points = standardizedSample.map((sq, i) => {
  const p = (i + 1 - 0.5) / n;
  return [invNormCdf(p), sq];
});
const tMin = points[0][0];
const tMax = points[points.length - 1][0];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "qq-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    top: 56,
    right: 70,
    textStyle: { color: t.ink, fontSize: 15 },
    itemWidth: 20,
    itemHeight: 12,
  },
  grid: { left: 100, right: 70, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Theoretical Quantiles",
    nameLocation: "middle",
    nameGap: 44,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Sample Quantiles (z-score)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Reaction times",
      type: "scatter",
      data: points,
      symbolSize: 12,
      itemStyle: { color: t.palette[0], opacity: 0.8 },
    },
    {
      name: "Reference (y = x)",
      type: "line",
      data: [[tMin, tMin], [tMax, tMax]],
      showSymbol: false,
      lineStyle: { color: t.ink, width: 2, type: "dashed" },
      z: 1,
    },
  ],
});
