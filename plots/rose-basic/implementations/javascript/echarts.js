// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 94/100 | Created: 2026-07-25

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Average monthly rainfall for a humid-subtropical coastal city (mm), Jan at
// the top, running clockwise — a classic natural-12-month cycle for a rose
// chart, with a monsoon-influenced Jun-Aug wet season.
const months = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const rainfall = [62, 58, 71, 85, 98, 112, 125, 118, 95, 82, 70, 65];
const peakIndex = rainfall.indexOf(Math.max(...rainfall));

// Highlight the wettest month with an ink outline and an explicit callout —
// the dual radius+color encoding already tells the story, this makes it explicit.
const seriesData = rainfall.map((value, i) =>
  i === peakIndex
    ? {
        value,
        itemStyle: { borderColor: t.ink, borderWidth: 3 },
        label: {
          show: true,
          position: "middle",
          formatter: () => `Peak · ${value} mm`,
          color: t.ink,
          fontSize: 12,
          fontWeight: 600,
        },
      }
    : value,
);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const title = "rose-basic · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    subtext: "Average monthly rainfall (mm) · humid-subtropical coastal city",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
    subtextStyle: { color: t.inkSoft, fontSize: 14, fontWeight: 400 },
  },
  tooltip: {
    formatter: (p) => `${p.name}: ${p.value} mm`,
  },
  polar: {
    center: ["50%", "55%"],
    radius: ["8%", "62%"],
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
    z: 10,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 12,
      formatter: "{value} mm",
      backgroundColor: t.pageBg,
      padding: [2, 4],
      borderRadius: 2,
    },
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
      z: 2,
      data: seriesData,
      barCategoryGap: "8%",
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 2,
        borderRadius: 4,
      },
      emphasis: { itemStyle: { borderColor: t.ink, borderWidth: 2 } },
    },
  ],
});
