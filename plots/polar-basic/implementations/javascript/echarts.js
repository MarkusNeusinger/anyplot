// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-07-24

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wind-direction frequency: percentage of observations the wind blew from
// each of the 16 compass points, with a prevailing wind out of the SW.
const directions = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
];
const prevailingIndex = directions.indexOf("SW");
const frequencies = directions.map((_, i) => {
  const steps = directions.length;
  const angularDist = Math.min(
    Math.abs(i - prevailingIndex),
    steps - Math.abs(i - prevailingIndex),
  );
  const gaussian = 27 * Math.exp(-(angularDist ** 2) / (2 * 3.2 ** 2));
  return Math.round((gaussian + 2.5) * 10) / 10;
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "polar-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  polar: {
    center: ["50%", "56%"],
    radius: "68%",
  },
  angleAxis: {
    type: "category",
    data: directions,
    startAngle: 90,
    clockwise: true,
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisLabel: { color: t.inkSoft, fontSize: 15 },
    splitLine: { lineStyle: { color: t.grid } },
  },
  radiusAxis: {
    type: "value",
    min: 0,
    axisLine: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    splitLine: { lineStyle: { color: t.grid } },
    splitNumber: 4,
  },
  series: [
    {
      type: "bar",
      coordinateSystem: "polar",
      data: frequencies,
      name: "Wind frequency",
      barCategoryGap: "20%",
      itemStyle: { color: t.palette[0] },
    },
  ],
});
