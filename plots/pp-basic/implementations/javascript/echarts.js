// anyplot.ai
// pp-basic: Probability-Probability (P-P) Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-09
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data -------------------------------------------------------------------
// Deterministic LCG for reproducibility (no seeded Math.random in browser)
let rngState = 42;
function lcgRand() {
  rngState = ((rngState * 1664525 + 1013904223) | 0) >>> 0;
  return rngState / 4294967296;
}

function randNormal() {
  const u1 = lcgRand();
  const u2 = lcgRand();
  return Math.sqrt(-2 * Math.log(u1 + 1e-10)) * Math.cos(2 * Math.PI * u2);
}

// 200 process measurement samples with mild right skew (positive half-normal component)
const n = 200;
const rawData = [];
for (let i = 0; i < n; i++) {
  const z = randNormal();
  const skew = Math.max(0, randNormal()) * 0.35;
  rawData.push(z + skew);
}

// Fit normal distribution parameters to the sample
const mean = rawData.reduce((a, b) => a + b, 0) / n;
const variance = rawData.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const std = Math.sqrt(variance);

// Normal CDF via Abramowitz & Stegun 7.1.26 (|error| < 1.5e-7)
function normalCDF(x) {
  const z = (x - mean) / (std * Math.SQRT2);
  const absZ = Math.abs(z);
  const t2 = 1 / (1 + 0.3275911 * absZ);
  const poly =
    (0.254829592 +
      t2 * (-0.284496736 + t2 * (1.421413741 + t2 * (-1.453152027 + t2 * 1.061405429)))) *
    t2;
  const erfc = poly * Math.exp(-absZ * absZ);
  return z >= 0 ? 1 - 0.5 * erfc : 0.5 * erfc;
}

// Sort and compute empirical CDF with Weibull plotting positions i/(n+1)
const sorted = [...rawData].sort((a, b) => a - b);
const scatterData = sorted.map((x, i) => [normalCDF(x), (i + 1) / (n + 1)]);

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  textStyle: { color: t.inkSoft },

  title: {
    text: "pp-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
  },

  legend: {
    data: ["Observations", "Perfect fit"],
    bottom: 24,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemGap: 24,
  },

  // Equal margins so the grid area is square (1200 - 120 - 80 = 1000 each axis)
  grid: { left: 120, right: 80, top: 90, bottom: 110 },

  xAxis: {
    type: "value",
    name: "Theoretical Cumulative Probability",
    nameLocation: "middle",
    nameGap: 52,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: 0,
    max: 1,
    interval: 0.25,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },

  yAxis: {
    type: "value",
    name: "Empirical Cumulative Probability",
    nameLocation: "middle",
    nameGap: 68,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: 0,
    max: 1,
    interval: 0.25,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },

  series: [
    {
      name: "Perfect fit",
      type: "line",
      data: [
        [0, 0],
        [1, 1],
      ],
      symbol: "none",
      lineStyle: { color: t.inkSoft, width: 2.5, type: "dashed" },
      z: 1,
    },
    {
      name: "Observations",
      type: "scatter",
      data: scatterData,
      symbolSize: 7,
      itemStyle: {
        color: t.palette[0],
        opacity: 0.75,
        borderColor: t.pageBg,
        borderWidth: 0.5,
      },
      z: 2,
    },
  ],
});
