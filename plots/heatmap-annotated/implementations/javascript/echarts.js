// anyplot.ai
// heatmap-annotated: Annotated Heatmap
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-08-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: correlation matrix of weather metrics (symmetric, diagonal = 1) -
const metrics = [
  "Temperature", "Humidity", "Wind Speed", "Pressure",
  "Rainfall", "Cloud Cover", "UV Index", "Visibility",
];

const corr = [
  [1.00, -0.42, -0.08, 0.35, -0.30, -0.25, 0.81, 0.40],
  [-0.42, 1.00, 0.15, -0.38, 0.62, 0.55, -0.48, -0.52],
  [-0.08, 0.15, 1.00, -0.20, 0.28, 0.18, -0.05, -0.22],
  [0.35, -0.38, -0.20, 1.00, -0.45, -0.30, 0.25, 0.33],
  [-0.30, 0.62, 0.28, -0.45, 1.00, 0.70, -0.40, -0.60],
  [-0.25, 0.55, 0.18, -0.30, 0.70, 1.00, -0.65, -0.48],
  [0.81, -0.48, -0.05, 0.25, -0.40, -0.65, 1.00, 0.45],
  [0.40, -0.52, -0.22, 0.33, -0.60, -0.48, 0.45, 1.00],
];

// --- Cell-background-aware annotation contrast --------------------------
// Interpolates the same imprint_div gradient the visualMap uses, so each
// cell's label color is derived from that exact cell's rendered background.
const hexToRgb = (hex) => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
];
const lerpChannel = (a, b, ratio) => Math.round(a + (b - a) * ratio);
const lerpRgb = (hexA, hexB, ratio) => {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return [lerpChannel(a[0], b[0], ratio), lerpChannel(a[1], b[1], ratio), lerpChannel(a[2], b[2], ratio)];
};
const divergingRgb = (value) => {
  const ratio = (value + 1) / 2; // value in [-1, 1] -> [0, 1]
  return ratio <= 0.5 ? lerpRgb(t.div[0], t.div[1], ratio / 0.5) : lerpRgb(t.div[1], t.div[2], (ratio - 0.5) / 0.5);
};
const luma = ([r, g, b]) => (r * 299 + g * 587 + b * 114) / 1000;
const contrastColor = (value) => (luma(divergingRgb(value)) > 140 ? "#1A1A17" : "#F0EFE8");

const cells = [];
for (let row = 0; row < metrics.length; row += 1) {
  for (let col = 0; col < metrics.length; col += 1) {
    const value = corr[row][col];
    cells.push({
      value: [col, row, value],
      label: { color: contrastColor(value) },
    });
  }
}

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "heatmap-annotated · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 175, right: 205, top: 110, bottom: 170 },
  xAxis: {
    type: "category",
    data: metrics,
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 14, rotate: 40 },
  },
  yAxis: {
    type: "category",
    data: metrics,
    inverse: true,
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
  },
  visualMap: {
    type: "continuous",
    min: -1,
    max: 1,
    calculable: true,
    orient: "vertical",
    right: 15,
    top: "middle",
    itemHeight: 360,
    itemWidth: 18,
    precision: 2,
    inRange: { color: t.div },
    textStyle: { color: t.inkSoft, fontSize: 13 },
  },
  series: [
    {
      type: "heatmap",
      data: cells,
      itemStyle: { borderColor: t.pageBg, borderWidth: 3 },
      label: {
        show: true,
        formatter: (params) => params.value[2].toFixed(2),
        fontSize: 13,
      },
      emphasis: {
        itemStyle: { shadowBlur: 0, borderColor: t.ink, borderWidth: 2 },
      },
    },
  ],
});
