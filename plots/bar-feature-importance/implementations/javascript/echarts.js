// anyplot.ai
// bar-feature-importance: Feature Importance Bar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Gradient-boosting churn model — feature_importances_ + per-tree std, ascending
// by importance so the category axis (bottom-to-top) puts the top driver on top.
const features = [
  "Partner Status",
  "Senior Citizen",
  "Dependents Count",
  "Paperless Billing",
  "Internet Service Type",
  "Tech Support Access",
  "Total Charges",
  "Payment Delay Days",
  "Support Tickets",
  "Monthly Charges",
  "Tenure Months",
  "Contract Length",
];
const importance = [0.013, 0.017, 0.020, 0.027, 0.034, 0.042, 0.058, 0.076, 0.099, 0.134, 0.208, 0.272];
const std = [0.006, 0.007, 0.008, 0.009, 0.010, 0.011, 0.014, 0.016, 0.019, 0.022, 0.028, 0.031];
const errorBarData = features.map((name, i) => [name, importance[i] - std[i], importance[i] + std[i]]);

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Error bar renderer (ECharts has no built-in error-bar series) ----------
// The precision label lives here, anchored past the high cap, so its position
// always clears the error bar regardless of how wide the std interval is.
function renderErrorBar(params, api) {
  const category = api.value(0);
  const centerValue = importance[params.dataIndex];
  const lowPoint = api.coord([api.value(1), category]);
  const highPoint = api.coord([api.value(2), category]);
  const capHalf = 7;
  const style = api.style({ stroke: t.ink, fill: undefined, lineWidth: 1.5 });
  return {
    type: "group",
    children: [
      { type: "line", shape: { x1: lowPoint[0], y1: lowPoint[1], x2: highPoint[0], y2: highPoint[1] }, style },
      { type: "line", shape: { x1: lowPoint[0], y1: lowPoint[1] - capHalf, x2: lowPoint[0], y2: lowPoint[1] + capHalf }, style },
      { type: "line", shape: { x1: highPoint[0], y1: highPoint[1] - capHalf, x2: highPoint[0], y2: highPoint[1] + capHalf }, style },
      {
        type: "text",
        style: {
          x: highPoint[0] + 12,
          y: highPoint[1],
          text: `${(centerValue * 100).toFixed(1)}%`,
          fill: t.inkSoft,
          fontSize: 14,
          verticalAlign: "middle",
          align: "left",
        },
      },
    ],
  };
}

// --- Option -------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "bar-feature-importance · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    valueFormatter: (v) => `${(v * 100).toFixed(1)}%`,
  },
  grid: { left: 24, right: 150, top: 100, bottom: 130, containLabel: true },
  xAxis: {
    type: "value",
    name: "Relative importance",
    nameLocation: "middle",
    nameGap: 36,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => `${Math.round(v * 100)}%` },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: features,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  visualMap: {
    type: "continuous",
    dimension: 0,
    min: 0,
    max: Math.max(...importance) * 1.05,
    calculable: false,
    orient: "horizontal",
    left: "center",
    bottom: 24,
    // Under orient:"horizontal" ECharts swaps the usual meaning: itemHeight is
    // the bar's length, itemWidth its thickness — the reverse of "vertical".
    itemWidth: 14,
    itemHeight: 260,
    text: ["High", "Low"],
    textStyle: { color: t.inkSoft, fontSize: 14 },
    inRange: { color: t.seq },
  },
  series: [
    {
      type: "bar",
      data: importance,
      barWidth: "62%",
    },
    {
      type: "custom",
      renderItem: renderErrorBar,
      encode: { x: [1, 2], y: 0 },
      data: errorBarData,
      z: 10,
      silent: true,
    },
  ],
});

chart.on("finished", () => {
  window.__anyplotReady = true;
});
