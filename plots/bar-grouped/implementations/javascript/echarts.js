// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue ($K) by product line across regions
// West flips the usual Electronics-leads rank order: an in-store apparel
// campaign put Apparel ahead of Electronics that quarter.
const regions = ["North", "South", "East", "West", "Central"];
const productLines = ["Electronics", "Apparel", "Home Goods"];
const revenue = {
  Electronics: [420, 380, 510, 340, 390],
  Apparel: [310, 340, 280, 460, 260],
  "Home Goods": [180, 210, 195, 220, 175],
};
const overallAverage =
  Object.values(revenue)
    .flat()
    .reduce((sum, v) => sum + v, 0) / (regions.length * productLines.length);

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
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    valueFormatter: (v) => `$${v}K`,
  },
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
    itemStyle: {
      color: t.palette[i],
      borderRadius: [4, 4, 0, 0],
      shadowBlur: 6,
      shadowColor: "rgba(0, 0, 0, 0.12)",
    },
    emphasis: { focus: "series" },
    barGap: "12%",
    barCategoryGap: "32%",
    ...(i === 0
      ? {
          markPoint: {
            symbol: "pin",
            symbolSize: 46,
            itemStyle: { color: t.palette[0] },
            label: { color: "#fff", fontSize: 12, fontWeight: 600, formatter: "${c}K" },
            data: [{ type: "max", name: "Peak" }],
          },
          markLine: {
            symbol: "none",
            lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
            label: {
              color: t.inkSoft,
              fontSize: 12,
              formatter: `Avg ${overallAverage.toFixed(0)}K`,
              position: "insideEndTop",
            },
            data: [{ yAxis: overallAverage, name: "Overall average" }],
          },
        }
      : {}),
  })),
});
