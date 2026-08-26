// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Splitting-criterion curves across the full probability range, 101 points for
// a smooth curve including both endpoints.
const POINT_COUNT = 101;
const probabilities = Array.from(
  { length: POINT_COUNT },
  (_, i) => i / (POINT_COUNT - 1),
);

const giniImpurity = probabilities.map((p) => 2 * p * (1 - p));
const entropy = probabilities.map((p) => {
  // Binary entropy in bits; the p*log2(p) term is defined as 0 at p=0 and p=1
  // (the standard 0*log(0) := 0 convention), so both endpoints render cleanly.
  const term = (x) => (x === 0 ? 0 : -x * Math.log2(x));
  return term(p) + term(1 - p);
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[0], t.palette[1]],
  backgroundColor: "transparent",
  title: {
    text: "line-impurity-comparison · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    top: 70,
    textStyle: { color: t.ink, fontSize: 16 },
    data: ["Gini = 2p(1−p)", "Entropy = −p·log₂p − (1−p)·log₂(1−p)"],
  },
  grid: { left: 90, right: 60, top: 150, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Probability p",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 1,
    interval: 0.1,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Impurity",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 1.15,
    interval: 0.25,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Gini = 2p(1−p)",
      type: "line",
      data: probabilities.map((p, i) => [p, giniImpurity[i]]),
      showSymbol: false,
      lineStyle: { width: 4, color: t.palette[0] },
      markLine: {
        symbol: "none",
        silent: true,
        animation: false,
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: { show: false },
        data: [{ xAxis: 0.5 }],
      },
      markPoint: {
        symbol: "circle",
        symbolSize: 14,
        animation: false,
        itemStyle: {
          color: t.palette[0],
          borderColor: t.pageBg,
          borderWidth: 2,
        },
        label: { show: false },
        data: [{ coord: [0.5, 0.5] }],
      },
    },
    {
      name: "Entropy = −p·log₂p − (1−p)·log₂(1−p)",
      type: "line",
      data: probabilities.map((p, i) => [p, entropy[i]]),
      showSymbol: false,
      lineStyle: { width: 4, color: t.palette[1] },
      markPoint: {
        symbol: "circle",
        symbolSize: 14,
        animation: false,
        itemStyle: {
          color: t.palette[1],
          borderColor: t.pageBg,
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: "p = 0.5 — max impurity",
          position: "top",
          offset: [95, -4],
          color: t.inkSoft,
          fontSize: 14,
        },
        data: [{ coord: [0.5, 1] }],
      },
    },
  ],
});
