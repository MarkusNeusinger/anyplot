// anyplot.ai
// residual-plot: Residual Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
let seed = 42;
const lcg = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};
const gaussian = () => {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

const n = 300;
const fitted = [];
const residuals = [];
for (let i = 0; i < n; i++) {
  const predictedMinutes = 15 + lcg() * 45; // predicted delivery time, 15-60 min
  const noiseScale = 1.2 + 0.06 * predictedMinutes; // mild heteroscedasticity
  fitted.push(predictedMinutes);
  residuals.push(gaussian() * noiseScale);
}

const mean = residuals.reduce((a, b) => a + b, 0) / n;
const variance = residuals.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const std = Math.sqrt(variance);
const outlierThreshold = 2.5 * std;

const normalPoints = [];
const outlierPoints = [];
fitted.forEach((value, i) => {
  const point = [value, residuals[i]];
  if (Math.abs(residuals[i]) > outlierThreshold) {
    outlierPoints.push(point);
  } else {
    normalPoints.push(point);
  }
});

const xMin = Math.floor(Math.min(...fitted) - 2);
const xMax = Math.ceil(Math.max(...fitted) + 2);
const bandLow = -2 * std;
const bandHigh = 2 * std;

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[0], t.palette[4]],
  backgroundColor: "transparent",
  title: {
    text: "residual-plot · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Normal", "Outlier (|z| > 2.5σ)"],
    top: 72,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 110, right: 60, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Predicted Delivery Time (min)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: xMin,
    max: xMax,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Residual (min)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Normal",
      type: "scatter",
      data: normalPoints,
      symbolSize: 12,
      itemStyle: { color: t.palette[0], opacity: 0.6 },
      markLine: {
        symbol: "none",
        silent: true,
        lineStyle: { color: t.ink, width: 2, type: "solid" },
        label: { show: false },
        data: [{ yAxis: 0 }],
      },
      markArea: {
        silent: true,
        itemStyle: { color: t.grid },
        data: [
          [
            { yAxis: bandLow, xAxis: "min" },
            { yAxis: bandHigh, xAxis: "max" },
          ],
        ],
      },
    },
    {
      name: "Outlier (|z| > 2.5σ)",
      type: "scatter",
      data: outlierPoints,
      symbolSize: 18,
      itemStyle: { color: t.palette[4], opacity: 0.9 },
    },
  ],
});
