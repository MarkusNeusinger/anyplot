// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: pending | Created: 2026-07-24
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Data — three phone models compared across six product attributes (0-100 scale)
const indicators = [
  { name: "Battery Life", max: 100 },
  { name: "Camera", max: 100 },
  { name: "Performance", max: 100 },
  { name: "Display", max: 100 },
  { name: "Price Value", max: 100 },
  { name: "Build Quality", max: 100 },
];

const models = [
  { name: "Aurora X", values: [78, 92, 95, 88, 45, 90] },
  { name: "Nimbus S", values: [85, 70, 72, 75, 78, 68] },
  { name: "Vega Lite", values: [90, 55, 50, 60, 92, 55] },
];

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "radar-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: models.map((m) => m.name),
    bottom: 20,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 20,
    itemHeight: 14,
  },
  radar: {
    center: ["50%", "54%"],
    radius: "60%",
    shape: "polygon",
    splitNumber: 5,
    indicator: indicators,
    name: { textStyle: { color: t.inkSoft, fontSize: 15 } },
    axisLine: { lineStyle: { color: t.grid } },
    splitLine: { lineStyle: { color: t.grid } },
    splitArea: { show: false },
  },
  series: [
    {
      type: "radar",
      data: models.map((m, i) => ({
        name: m.name,
        value: m.values,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: t.palette[i], width: 3 },
        itemStyle: { color: t.palette[i] },
        areaStyle: { color: t.palette[i], opacity: 0.25 },
      })),
    },
  ],
});
