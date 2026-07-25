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
const rawWeights = directions.map((_, i) => {
  const steps = directions.length;
  const angularDist = Math.min(
    Math.abs(i - prevailingIndex),
    steps - Math.abs(i - prevailingIndex),
  );
  const gaussian = 27 * Math.exp(-(angularDist ** 2) / (2 * 3.2 ** 2));
  return gaussian + 2.5;
});
const weightSum = rawWeights.reduce((sum, w) => sum + w, 0);
const frequencies = rawWeights.map(
  (w) => Math.round((w / weightSum) * 1000) / 10,
);

// Fill opacity ramps with value (deeper toward the prevailing direction); the
// stroke stays at full brand-green opacity as a light outline on every petal.
function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const maxFrequency = Math.max(...frequencies);

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
    name: "Frequency (%)",
    nameTextStyle: { color: t.inkSoft, fontSize: 13 },
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
      data: frequencies.map((value) => ({
        value,
        itemStyle: {
          color: withAlpha(t.palette[0], 0.55 + 0.45 * (value / maxFrequency)),
          borderColor: t.palette[0],
          borderWidth: 1,
        },
      })),
      name: "Wind frequency",
      barCategoryGap: "20%",
    },
  ],
});
