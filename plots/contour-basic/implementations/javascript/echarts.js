// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 78/100 | Created: 2026-06-25
//# anyplot-orientation: square

// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// Grid: 61 points from -3.0 to 3.0 (step=0.1) — nice round axis labels
const N = 61;
const xVals = [];
const yVals = [];
for (let i = 0; i < N; i++) {
  const v = parseFloat((-3 + i * 0.1).toFixed(1));
  xVals.push(v);
  yVals.push(v);
}

// Bivariate Gaussian density: two distinct peaks
function density(x, y) {
  const g1 = Math.exp(-((x - 1.3) ** 2 + (y - 1.0) ** 2) / (2 * 0.36));
  const g2 = 0.85 * Math.exp(-((x + 1.0) ** 2 + (y + 1.0) ** 2) / (2 * 0.64));
  return g1 + g2;
}

let minVal = Infinity;
let maxVal = -Infinity;
const gridData = [];
for (let yi = 0; yi < N; yi++) {
  for (let xi = 0; xi < N; xi++) {
    const z = density(xVals[xi], yVals[yi]);
    gridData.push([xi, yi, z]);
    if (z < minVal) minVal = z;
    if (z > maxVal) maxVal = z;
  }
}

const xLabels = xVals.map(v => v.toFixed(1));
const yLabels = yVals.map(v => v.toFixed(1));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "contour-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 24, fontWeight: "bold" }
  },
  grid: { left: 100, right: 155, top: 90, bottom: 100 },
  xAxis: {
    type: "category",
    data: xLabels,
    name: "X",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 9 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },
  yAxis: {
    type: "category",
    data: yLabels,
    name: "Y",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 9 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },
  visualMap: {
    min: minVal,
    max: maxVal,
    calculable: false,
    orient: "vertical",
    right: 25,
    top: "center",
    inRange: { color: t.seq },
    textStyle: { color: t.inkSoft, fontSize: 13 },
    text: ["High", "Low"],
    formatter: v => v.toFixed(2)
  },
  series: [{
    type: "heatmap",
    data: gridData,
    emphasis: { disabled: true }
  }]
});
