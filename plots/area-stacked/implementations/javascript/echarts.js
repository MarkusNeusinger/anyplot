// anyplot.ai
// area-stacked: Stacked Area Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// US electricity consumption by sector, 2010-2024 (TWh, illustrative)
const years = Array.from({ length: 15 }, (_, i) => String(2010 + i));

const industrial = [480, 478, 482, 485, 488, 490, 492, 495, 498, 500, 502, 505, 508, 510, 512];
const residential = [385, 390, 388, 395, 400, 398, 405, 410, 408, 415, 420, 418, 425, 430, 428];
const commercial = [310, 315, 318, 322, 328, 330, 335, 340, 345, 350, 355, 358, 362, 368, 372];
const transportation = [8, 10, 13, 17, 22, 28, 35, 44, 54, 66, 80, 96, 114, 134, 156];

const series = [
  { name: "Industrial", data: industrial },
  { name: "Residential", data: residential },
  { name: "Commercial", data: commercial },
  { name: "Transportation", data: transportation },
];

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "area-stacked · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  tooltip: { trigger: "axis" },
  legend: {
    bottom: 10,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 18,
    itemHeight: 12,
  },
  grid: { left: 90, right: 60, top: 100, bottom: 90 },
  xAxis: {
    type: "category",
    data: years,
    boundaryGap: false,
    name: "Year",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    name: "Electricity Consumption (TWh)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: series.map((s, i) => ({
    name: s.name,
    type: "line",
    stack: "total",
    smooth: 0.2,
    showSymbol: false,
    lineStyle: { width: 2, color: t.palette[i] },
    itemStyle: { color: t.palette[i] },
    areaStyle: { color: t.palette[i], opacity: 0.82 },
    emphasis: { focus: "series" },
    data: s.data,
  })),
});
