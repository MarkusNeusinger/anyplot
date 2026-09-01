// anyplot.ai
// coefficient-confidence: Coefficient Plot with Confidence Intervals
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Predictors of weekly e-commerce conversion rate (percentage-point effect),
// ordered by absolute coefficient magnitude, descending.
const rows = [
  { variable: "Mobile Optimization Score", coefficient: 4.8, ciLower: 2.1, ciUpper: 7.5, significant: true },
  { variable: "Checkout Steps", coefficient: -3.9, ciLower: -6.4, ciUpper: -1.4, significant: true },
  { variable: "Free Shipping Offer", coefficient: 3.2, ciLower: 0.9, ciUpper: 5.5, significant: true },
  { variable: "Page Load Speed", coefficient: -2.7, ciLower: -5.0, ciUpper: -0.4, significant: true },
  { variable: "Popup Ads", coefficient: -2.1, ciLower: -4.6, ciUpper: 0.4, significant: false },
  { variable: "Product Reviews Count", coefficient: 1.8, ciLower: -0.3, ciUpper: 3.9, significant: false },
  { variable: "Live Chat Support", coefficient: 1.5, ciLower: -0.8, ciUpper: 3.8, significant: false },
  { variable: "Email Campaign Frequency", coefficient: 1.1, ciLower: -1.2, ciUpper: 3.4, significant: false },
  { variable: "Search Bar Prominence", coefficient: 0.6, ciLower: -1.7, ciUpper: 2.9, significant: false },
  { variable: "Loyalty Points Program", coefficient: 0.3, ciLower: -2.0, ciUpper: 2.6, significant: false },
];
const indexed = rows.map((r, i) => ({ ...r, idx: i }));
const categories = rows.map((r) => r.variable);
const significant = indexed.filter((r) => r.significant);
const notSignificant = indexed.filter((r) => !r.significant);

// --- Custom-series renderer for horizontal confidence-interval whiskers -----
function whiskerRenderItem(color, lineWidth) {
  return function (params, api) {
    const categoryIndex = api.value(0);
    const low = api.coord([api.value(1), categoryIndex]);
    const high = api.coord([api.value(2), categoryIndex]);
    const capHalf = 9;
    const style = { stroke: color, lineWidth };
    return {
      type: "group",
      children: [
        { type: "line", shape: { x1: low[0], y1: low[1] - capHalf, x2: low[0], y2: low[1] + capHalf }, style },
        { type: "line", shape: { x1: high[0], y1: high[1] - capHalf, x2: high[0], y2: high[1] + capHalf }, style },
        { type: "line", shape: { x1: low[0], y1: low[1], x2: high[0], y2: high[1] }, style },
      ],
    };
  };
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Website Conversion Drivers · coefficient-confidence · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 17, fontWeight: 500 },
  },
  legend: {
    data: ["Significant", "Not significant"],
    top: 90,
    itemWidth: 16,
    itemHeight: 16,
    textStyle: { color: t.inkSoft, fontSize: 15 },
  },
  grid: { left: 60, right: 90, top: 150, bottom: 100, containLabel: true },
  xAxis: {
    type: "value",
    name: "Coefficient Estimate (percentage points)",
    nameLocation: "center",
    nameGap: 42,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: categories,
    inverse: true,
    axisLabel: { color: t.inkSoft, fontSize: 15 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "custom",
      name: "__whisker_sig",
      silent: true,
      renderItem: whiskerRenderItem(t.palette[0], 2.5),
      encode: { x: [1, 2], y: 0 },
      data: significant.map((r) => [r.idx, r.ciLower, r.ciUpper]),
      z: 2,
    },
    {
      type: "custom",
      name: "__whisker_notsig",
      silent: true,
      renderItem: whiskerRenderItem(t.inkSoft, 1.5),
      encode: { x: [1, 2], y: 0 },
      data: notSignificant.map((r) => [r.idx, r.ciLower, r.ciUpper]),
      z: 2,
    },
    {
      name: "Significant",
      type: "scatter",
      symbolSize: 18,
      itemStyle: { color: t.palette[0] },
      data: significant.map((r) => [r.coefficient, r.idx]),
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        lineStyle: { color: t.ink, type: "dashed", width: 1.5 },
        data: [{ xAxis: 0 }],
      },
      z: 3,
    },
    {
      name: "Not significant",
      type: "scatter",
      symbolSize: 18,
      itemStyle: { color: t.inkSoft },
      data: notSignificant.map((r) => [r.coefficient, r.idx]),
      z: 3,
    },
  ],
});
