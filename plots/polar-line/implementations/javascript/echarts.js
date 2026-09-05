// anyplot.ai
// polar-line: Polar Line Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Average monthly temperature (°C) for two hemispheres — opposite seasonal phase.
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const northernHemisphere = [0, 1, 6, 12, 18, 23, 26, 25, 21, 15, 9, 3];
const southernHemisphere = [23, 23, 22, 19, 16, 13, 12, 13, 16, 18, 20, 22];

// A category angleAxis would break alignment if a 13th slot were appended just
// to close the loop, so the axis runs on a continuous 0-12 value scale instead
// (one unit per month) and each series repeats its January value at month 12 —
// same angle as month 0 — to draw a fully closed ring. Polar series data pairs
// are [radiusValue, angleValue] (radiusAxis is dimension 0), not the reverse.
const closeLoop = (values) => values.map((v, i) => [v, i]).concat([[values[0], 12]]);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "polar-line · javascript · echarts · anyplot.ai",
    left: "center",
    top: 10,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    bottom: 10,
    data: ["Northern hemisphere", "Southern hemisphere"],
    textStyle: { color: t.ink, fontSize: 16 },
  },
  polar: { center: ["50%", "54%"], radius: "62%" },
  angleAxis: {
    type: "value",
    min: 0,
    max: 12,
    interval: 1,
    startAngle: 90,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (value) => months[value] || "" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  radiusAxis: {
    type: "value",
    min: -5,
    max: 30,
    axisLabel: { color: t.inkSoft, fontSize: 13, formatter: "{value}°C" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Northern hemisphere",
      type: "line",
      coordinateSystem: "polar",
      data: closeLoop(northernHemisphere),
      symbol: "circle",
      symbolSize: 9,
      lineStyle: { width: 3.5 },
    },
    {
      name: "Southern hemisphere",
      type: "line",
      coordinateSystem: "polar",
      data: closeLoop(southernHemisphere),
      symbol: "circle",
      symbolSize: 9,
      lineStyle: { width: 3.5 },
    },
  ],
});
