// anyplot.ai
// curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// model_complexity spans 1..20 (e.g. polynomial degree / tree depth)
const N = 60;
const complexity = Array.from({ length: N }, (_, i) => 1 + (i * 19) / (N - 1));

const biasSquared = complexity.map((c) => 4 / (1 + 0.55 * c) + 0.15);
const variance = complexity.map((c) => 0.012 * c * c + 0.03);
const irreducible = complexity.map(() => 0.35);
const totalError = complexity.map((_, i) => biasSquared[i] + variance[i] + irreducible[i]);

// Find the optimal complexity (minimum total error)
let optIdx = 0;
for (let i = 1; i < N; i++) {
  if (totalError[i] < totalError[optIdx]) optIdx = i;
}
const optComplexity = complexity[optIdx];
const optError = totalError[optIdx];

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[0], t.palette[2], t.palette[4], t.palette[6]],
  backgroundColor: "transparent",
  title: {
    text: "curve-bias-variance-tradeoff · javascript · echarts · anyplot.ai",
    left: "center",
    top: 12,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  grid: { left: 90, right: 170, top: 150, bottom: 90 },
  legend: {
    top: 60,
    textStyle: { color: t.ink, fontSize: 15 },
    itemWidth: 26,
    itemHeight: 3,
  },
  xAxis: {
    type: "value",
    name: "Model Complexity",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 1,
    max: 20,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Prediction Error",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Bias²",
      type: "line",
      data: complexity.map((c, i) => [c, biasSquared[i]]),
      showSymbol: false,
      lineStyle: { width: 3.5, color: t.palette[0] },
      endLabel: {
        show: true,
        formatter: "{a}",
        color: t.palette[0],
        fontSize: 14,
        fontWeight: 500,
        distance: 10,
        offset: [0, -16],
      },
      z: 3,
      markArea: {
        silent: true,
        itemStyle: { color: t.palette[0], opacity: 0.1 },
        label: { position: "insideTop", color: t.inkSoft, fontSize: 15 },
        data: [[{ xAxis: 1, name: "Underfitting zone" }, { xAxis: optComplexity }]],
      },
    },
    {
      name: "Variance",
      type: "line",
      data: complexity.map((c, i) => [c, variance[i]]),
      showSymbol: false,
      lineStyle: { width: 3.5, color: t.palette[2] },
      endLabel: {
        show: true,
        formatter: "{a}",
        color: t.palette[2],
        fontSize: 14,
        fontWeight: 500,
        distance: 10,
      },
      z: 3,
      markArea: {
        silent: true,
        itemStyle: { color: t.palette[2], opacity: 0.1 },
        label: { position: "insideTop", color: t.inkSoft, fontSize: 15 },
        data: [[{ xAxis: optComplexity, name: "Overfitting zone" }, { xAxis: 20 }]],
      },
    },
    {
      name: "Irreducible Error",
      type: "line",
      data: complexity.map((c, i) => [c, irreducible[i]]),
      showSymbol: false,
      lineStyle: { width: 2.5, color: t.palette[6], type: "dashed" },
      endLabel: {
        show: true,
        formatter: "{a}",
        color: t.palette[6],
        fontSize: 14,
        fontWeight: 500,
        distance: 10,
        offset: [0, 16],
      },
      z: 2,
    },
    {
      name: "Total Error",
      type: "line",
      data: complexity.map((c, i) => [c, totalError[i]]),
      showSymbol: false,
      lineStyle: { width: 4, color: t.palette[4] },
      endLabel: {
        show: true,
        formatter: "{a}",
        color: t.palette[4],
        fontSize: 14,
        fontWeight: 600,
        distance: 10,
      },
      z: 4,
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.ink, type: "dashed", width: 1.5 },
        label: {
          formatter: "Optimal complexity",
          color: t.ink,
          fontSize: 14,
          position: "insideEndTop",
        },
        data: [{ xAxis: optComplexity }],
      },
      markPoint: {
        silent: true,
        symbol: "circle",
        symbolSize: 14,
        itemStyle: { color: t.palette[4], borderColor: t.pageBg, borderWidth: 2 },
        label: { show: false },
        data: [{ coord: [optComplexity, optError] }],
      },
    },
  ],
  graphic: [
    {
      type: "text",
      left: 90,
      top: 110,
      style: {
        text: "Total Error = Bias² + Variance + Irreducible Error",
        fill: t.inkSoft,
        fontSize: 15,
        fontStyle: "italic",
      },
    },
  ],
});
