// anyplot.ai
// polar-bar: Polar Bar Chart (Wind Rose)
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wind-rose observations: hourly frequency counts by compass direction and
// wind-speed bin. Prevailing westerlies with a secondary southerly lobe.
const directions = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
];
const speedBins = ["0-5 kt", "5-10 kt", "10-15 kt", "15-20 kt", "20+ kt"];
const frequencies = [
  [8, 6, 3, 1, 0], // N
  [6, 5, 2, 1, 0], // NNE
  [5, 4, 2, 1, 0], // NE
  [4, 3, 2, 1, 0], // ENE
  [4, 3, 1, 1, 0], // E
  [3, 3, 1, 1, 0], // ESE
  [4, 3, 2, 1, 0], // SE
  [5, 5, 3, 1, 0], // SSE
  [7, 8, 5, 2, 0], // S
  [9, 11, 9, 4, 1], // SSW
  [11, 15, 15, 8, 3], // SW
  [10, 16, 17, 11, 4], // WSW
  [9, 13, 13, 8, 3], // W
  [6, 9, 8, 5, 2], // WNW
  [5, 6, 5, 3, 1], // NW
  [5, 5, 4, 2, 0], // NNW
];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const series = speedBins.map((bin, binIndex) => ({
  name: bin,
  type: "bar",
  coordinateSystem: "polar",
  stack: "wind",
  data: frequencies.map((row) => row[binIndex]),
  itemStyle: { color: t.palette[binIndex] },
}));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "polar-bar · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    bottom: 16,
    left: "center",
    itemWidth: 16,
    itemHeight: 16,
    textStyle: { color: t.ink, fontSize: 15 },
  },
  polar: { center: ["50%", "54%"], radius: "62%" },
  angleAxis: {
    type: "category",
    data: directions,
    startAngle: 90,
    clockwise: true,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  radiusAxis: {
    type: "value",
    name: "Hours observed",
    nameTextStyle: { color: t.inkSoft, fontSize: 13 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series,
});
