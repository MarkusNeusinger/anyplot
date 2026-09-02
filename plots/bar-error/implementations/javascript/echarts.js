// anyplot.ai
// bar-error: Bar Chart with Error Bars
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Mean crop yield by fertilizer treatment, kg per plot (n = 30 plots each),
// with error bars showing ±1 standard deviation.
const categories = ["Control", "Nitrogen", "Phosphorus", "Potassium", "N+P+K", "Compost"];
const means = [18.4, 24.7, 21.3, 22.9, 29.6, 26.1];
const sds = [2.1, 2.8, 2.4, 2.5, 3.1, 2.7];
const rows = categories.map((category, idx) => ({
  idx,
  category,
  low: means[idx] - sds[idx],
  high: means[idx] + sds[idx],
}));
const maxWithError = Math.max(...means.map((m, i) => m + sds[i]));

// --- Custom-series renderer for vertical error-bar whiskers -----------------
function whiskerRenderItem(params, api) {
  const categoryIndex = api.value(0);
  const low = api.coord([categoryIndex, api.value(1)]);
  const high = api.coord([categoryIndex, api.value(2)]);
  const capHalf = 16;
  const style = { stroke: t.ink, lineWidth: 2.5 };
  return {
    type: "group",
    children: [
      { type: "line", shape: { x1: low[0] - capHalf, y1: low[1], x2: low[0] + capHalf, y2: low[1] }, style },
      { type: "line", shape: { x1: high[0] - capHalf, y1: high[1], x2: high[0] + capHalf, y2: high[1] }, style },
      { type: "line", shape: { x1: low[0], y1: low[1], x2: high[0], y2: high[1] }, style },
    ],
  };
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "bar-error · javascript · echarts · anyplot.ai",
    subtext: "Error bars represent ±1 standard deviation (n = 30 plots per treatment)",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  grid: { left: 90, right: 60, top: 160, bottom: 90, containLabel: true },
  xAxis: {
    type: "category",
    data: categories,
    name: "Treatment",
    nameLocation: "center",
    nameGap: 48,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    max: Math.ceil(maxWithError * 1.15),
    name: "Yield (kg per plot)",
    nameLocation: "center",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "bar",
      name: "Mean yield",
      barWidth: "48%",
      itemStyle: { color: t.palette[0] },
      data: means,
      z: 2,
    },
    {
      type: "custom",
      name: "__error_bars",
      silent: true,
      renderItem: whiskerRenderItem,
      encode: { x: 0, y: [1, 2] },
      data: rows.map((r) => [r.idx, r.low, r.high]),
      z: 3,
    },
  ],
});
