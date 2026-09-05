// anyplot.ai
// line-styled: Styled Line Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly average temperature by city, Jan–Dec (°C)
const months = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const berlin = [1, 2, 6, 10, 15, 18, 20, 20, 16, 11, 6, 2];
const madrid = [7, 9, 12, 14, 18, 23, 27, 27, 22, 16, 11, 8];
const oslo = [-4, -3, 1, 6, 12, 16, 18, 17, 12, 6, 1, -3];
const cairo = [14, 15, 18, 22, 26, 28, 29, 29, 27, 24, 19, 15];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Monthly Temperature by City · line-styled · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 18, fontWeight: 500 },
  },
  legend: {
    top: 68,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemWidth: 28,
    itemHeight: 3,
  },
  grid: { left: 90, right: 60, top: 130, bottom: 70 },
  xAxis: {
    type: "category",
    data: months,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Avg. Temperature (°C)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 15 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Berlin",
      type: "line",
      data: berlin,
      lineStyle: { type: "solid", width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      symbol: "none",
    },
    {
      name: "Madrid",
      type: "line",
      data: madrid,
      lineStyle: { type: "dashed", width: 3, color: t.palette[1] },
      itemStyle: { color: t.palette[1] },
      symbol: "none",
    },
    {
      name: "Oslo",
      type: "line",
      data: oslo,
      lineStyle: { type: "dotted", width: 3, color: t.palette[2] },
      itemStyle: { color: t.palette[2] },
      symbol: "none",
    },
    {
      name: "Cairo",
      type: "line",
      data: cairo,
      lineStyle: { type: [8, 4, 2, 4], width: 3, color: t.palette[3] },
      itemStyle: { color: t.palette[3] },
      symbol: "none",
    },
  ],
});
