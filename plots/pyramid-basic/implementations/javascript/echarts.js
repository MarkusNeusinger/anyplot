// anyplot.ai
// pyramid-basic: Basic Pyramid Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Population by age group, thousands of residents
const ageGroups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"];
const malePopulation = [42, 45, 47, 44, 39, 33, 24, 15];
const femalePopulation = [40, 43, 45, 43, 40, 36, 29, 22];
const axisMax = 50;

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
// Three-grid layout: left bars (male) + centered label column (age groups) +
// right bars (female), so the shared category axis sits on the pyramid's
// central spine instead of on one outer edge.
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "pyramid-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: ["Male", "Female"],
    top: 78,
    textStyle: { color: t.inkSoft, fontSize: 14 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    valueFormatter: (value) => `${Math.abs(value)}k`,
  },
  grid: [
    { left: "4%", width: "42%", top: 150, bottom: 90 },
    { left: "46%", width: "8%", top: 150, bottom: 90 },
    { left: "54%", width: "42%", top: 150, bottom: 90 },
  ],
  xAxis: [
    {
      type: "value",
      gridIndex: 0,
      inverse: true,
      min: 0,
      max: axisMax,
      axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}k" },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    { type: "value", gridIndex: 1, min: 0, max: 1, show: false },
    {
      type: "value",
      gridIndex: 2,
      min: 0,
      max: axisMax,
      axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}k" },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
  ],
  yAxis: [
    { type: "category", gridIndex: 0, data: ageGroups, show: false },
    {
      type: "category",
      gridIndex: 1,
      data: ageGroups,
      position: "left",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: t.ink, fontSize: 14, align: "left", margin: 0 },
    },
    { type: "category", gridIndex: 2, data: ageGroups, show: false },
  ],
  series: [
    {
      name: "Male",
      type: "bar",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: malePopulation,
      barWidth: "65%",
      itemStyle: { color: t.palette[0] },
    },
    {
      name: "Female",
      type: "bar",
      xAxisIndex: 2,
      yAxisIndex: 2,
      data: femalePopulation,
      barWidth: "65%",
      itemStyle: { color: t.palette[1] },
    },
  ],
});
