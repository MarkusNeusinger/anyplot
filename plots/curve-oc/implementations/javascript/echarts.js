// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-20
//# anyplot-orientation: landscape
// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// Binomial coefficient (numerically stable for n <= 200)
function binomCoeff(n, k) {
  if (k === 0 || k === n) return 1;
  if (k > n - k) k = n - k;
  let c = 1;
  for (let i = 0; i < k; i++) c = (c * (n - i)) / (i + 1);
  return c;
}

// P(accept | n, c, p) = sum_{k=0}^{c} C(n,k) * p^k * (1-p)^(n-k)
function ocProb(n, c, p) {
  if (p <= 0) return 1;
  if (p >= 1) return 0;
  let sum = 0;
  for (let k = 0; k <= c; k++) {
    sum += binomCoeff(n, k) * Math.pow(p, k) * Math.pow(1 - p, n - k);
  }
  return Math.min(1, Math.max(0, sum));
}

// --- Data -------------------------------------------------------------------
const X_MAX = 0.20;
const pVals = Array.from({ length: 201 }, (_, i) => (i * X_MAX) / 200);

const AQL  = 0.02;   // Acceptable Quality Level
const LTPD = 0.10;   // Lot Tolerance Percent Defective

const PLANS = [
  { n:  50, c: 1, label: "n=50, c=1"  },
  { n:  50, c: 2, label: "n=50, c=2"  },
  { n: 100, c: 2, label: "n=100, c=2" },
  { n: 100, c: 3, label: "n=100, c=3" },
];

const curveSeries = PLANS.map((plan, idx) => ({
  name: plan.label,
  type: "line",
  data: pVals.map((p) => [+(p.toFixed(6)), +(ocProb(plan.n, plan.c, p).toFixed(6))]),
  lineStyle: { width: 3.5, color: t.palette[idx] },
  itemStyle: { color: t.palette[idx] },
  symbol: "none",
  z: 3,
}));

// Reference lines on the first series: AQL/LTPD vertical, risk thresholds horizontal
curveSeries[0].markLine = {
  silent: true,
  symbol: "none",
  animation: false,
  lineStyle: { type: "dashed", color: t.inkSoft, width: 1.5, opacity: 0.65 },
  label: {
    show: true,
    fontSize: 13,
    color: t.inkSoft,
    formatter: "{b}",
  },
  data: [
    { name: "AQL (2%)",   xAxis: AQL,  label: { position: "insideEndTop" } },
    { name: "LTPD (10%)", xAxis: LTPD, label: { position: "insideEndTop" } },
    { name: "1−α = 95%", yAxis: 0.95, label: { position: "insideEndTop" } },
    { name: "β = 10%",        yAxis: 0.10, label: { position: "insideEndTop" } },
  ],
};

// --- Chart ------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "curve-oc · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "500" },
  },
  subtitle: {
    text: "Acceptance Sampling Plans — Probability of Acceptance vs Fraction Defective",
    left: "center",
    top: 58,
    textStyle: { color: t.inkSoft, fontSize: 15 },
  },
  legend: {
    top: 100,
    right: 36,
    orient: "vertical",
    textStyle: { color: t.ink, fontSize: 16 },
    itemGap: 14,
    itemWidth: 28,
    itemHeight: 4,
  },
  grid: { left: 120, right: 200, top: 145, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Fraction Defective (p)",
    nameLocation: "middle",
    nameGap: 52,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: X_MAX,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: (v) => (v * 100).toFixed(0) + "%",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Probability of Acceptance",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: 1,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: (v) => (v * 100).toFixed(0) + "%",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  tooltip: {
    trigger: "axis",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 14 },
    formatter: (params) => {
      const p = params[0].data[0];
      let s = `<b>p = ${(p * 100).toFixed(1)}%</b><br/>`;
      params.forEach((item) => {
        s += `${item.marker} ${item.seriesName}: ${(item.data[1] * 100).toFixed(1)}%<br/>`;
      });
      return s;
    },
  },
  series: curveSeries,
});
