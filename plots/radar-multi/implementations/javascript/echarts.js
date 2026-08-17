//# anyplot-orientation: square
// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const indicators = [
  { name: "Sound Quality", max: 100 },
  { name: "Battery Life", max: 100 },
  { name: "Comfort", max: 100 },
  { name: "Noise Cancel.", max: 100 },
  { name: "Value", max: 100 },
  { name: "Durability", max: 100 },
];

const earbuds = [
  { name: "AudioMax Pro", value: [88, 72, 80, 92, 60, 75] },
  { name: "SoundWave Elite", value: [70, 90, 85, 65, 78, 82] },
  { name: "EchoBuds Plus", value: [78, 68, 92, 74, 88, 70] },
];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "radar-multi · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },
  legend: {
    data: earbuds.map((s) => s.name),
    bottom: 16,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 18,
    itemHeight: 12,
  },
  radar: {
    indicator: indicators,
    center: ["50%", "52%"],
    radius: "74%",
    splitNumber: 5,
    axisName: { color: t.inkSoft, fontSize: 15 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    axisLabel: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
    splitArea: { show: false },
  },
  series: [
    {
      type: "radar",
      symbol: "circle",
      symbolSize: 6,
      data: earbuds.map((s, i) => ({
        name: s.name,
        value: s.value,
        lineStyle: { color: t.palette[i], width: 3 },
        areaStyle: { color: t.palette[i], opacity: 0.22 },
        itemStyle: { color: t.palette[i] },
      })),
    },
  ],
});
