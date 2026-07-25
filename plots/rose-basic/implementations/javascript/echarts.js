// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-07-25

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Average monthly rainfall for a temperate coastal city (mm), Jan at the top,
// running clockwise — a classic natural-12-month cycle for a rose chart.
const months = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const rainfall = [62, 58, 71, 85, 98, 112, 125, 118, 95, 82, 70, 65];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const title = "rose-basic · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  tooltip: {
    formatter: (p) => `${p.name}: ${p.value} mm`,
  },
  polar: {
    center: ["50%", "53%"],
    radius: "62%",
  },
  angleAxis: {
    type: "category",
    data: months,
    startAngle: 90,
    clockwise: true,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 16 },
    splitLine: { show: false },
  },
  radiusAxis: {
    type: "value",
    min: 0,
    max: 150,
    interval: 30,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 12, formatter: "{value} mm" },
    splitLine: { lineStyle: { color: t.grid } },
  },
  visualMap: {
    type: "continuous",
    min: Math.min(...rainfall),
    max: Math.max(...rainfall),
    dimension: 0,
    seriesIndex: 0,
    orient: "horizontal",
    left: "center",
    bottom: 30,
    itemWidth: 16,
    itemHeight: 220,
    text: ["More rain", "Less rain"],
    textStyle: { color: t.inkSoft, fontSize: 13 },
    inRange: { color: t.seq },
  },
  series: [
    {
      type: "bar",
      coordinateSystem: "polar",
      data: rainfall,
      barCategoryGap: "8%",
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 2,
      },
      emphasis: { itemStyle: { borderColor: t.ink, borderWidth: 2 } },
    },
  ],
});
