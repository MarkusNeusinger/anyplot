// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 82/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue ($K) by product line across regions
const regions = ["North", "South", "East", "West", "Central"];
const productLines = ["Electronics", "Apparel", "Home Goods"];
const revenue = {
  Electronics: [420, 380, 510, 460, 390],
  Apparel: [310, 340, 280, 300, 260],
  "Home Goods": [180, 210, 195, 220, 175],
};

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bar-grouped · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: productLines,
    top: 90,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 18,
    itemHeight: 12,
  },
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  grid: { left: 110, right: 60, top: 160, bottom: 80 },
  xAxis: {
    type: "category",
    data: regions,
    name: "Region",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Revenue ($K)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: productLines.map((name, i) => ({
    name,
    type: "bar",
    data: revenue[name],
    itemStyle: { color: t.palette[i] },
    barGap: "12%",
    barCategoryGap: "32%",
  })),
});
