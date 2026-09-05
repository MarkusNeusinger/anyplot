// anyplot.ai
// pdp-basic: Partial Dependence Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
// The harness only exposes pageBg/elevatedBg/ink/inkSoft/grid/palette/amber/seq/div —
// the "muted" semantic anchor (confidence-band fill) isn't a token field, so it's
// derived here the same way the Python reference snippet derives INK_MUTED.
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Gradient-boosting model predicting crop yield; partial dependence of the
// "rainfall" feature, averaged over all other features, centered at zero.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const GRID_POINTS = 60;
const R_MIN = 200;
const R_MAX = 1400;

function rawResponse(r) {
  const logistic = 3.0 / (1 + Math.exp(-(r - 550) / 140));
  const waterlogging = r > 900 ? 0.0000009 * Math.pow(r - 900, 2) : 0;
  return logistic - waterlogging;
}

const featureValues = [];
const rawCurve = [];
for (let i = 0; i < GRID_POINTS; i++) {
  const r = R_MIN + (i * (R_MAX - R_MIN)) / (GRID_POINTS - 1);
  featureValues.push(r);
  rawCurve.push(rawResponse(r));
}
const meanResponse = rawCurve.reduce((a, b) => a + b, 0) / rawCurve.length;
const partialDependence = rawCurve.map((v) => v - meanResponse);

// Pointwise confidence half-width — widest at the tails, where training
// samples (see rug plot below) are sparse and the estimate is less certain.
const DATA_CENTER = 650;
const halfWidth = featureValues.map(
  (r) => 0.15 + 0.9 * Math.pow(Math.abs(r - DATA_CENTER) / DATA_CENTER, 1.4)
);
const ciLower = partialDependence.map((v, i) => v - halfWidth[i]);
const ciBandHeight = halfWidth.map((h) => 2 * h);

// ECharts pairs series data against an implicit index on a continuous
// "value" xAxis unless each point is given explicitly as [x, y].
const partialDependenceXY = featureValues.map((r, i) => [r, partialDependence[i]]);
const ciLowerXY = featureValues.map((r, i) => [r, ciLower[i]]);
const ciBandHeightXY = featureValues.map((r, i) => [r, ciBandHeight[i]]);

// Training-data rug: rainfall samples clustered around the data center.
const RUG_SAMPLES = 70;
const rugValues = [];
for (let i = 0; i < RUG_SAMPLES; i++) {
  const r = Math.min(R_MAX, Math.max(R_MIN, DATA_CENTER + gaussian() * 180));
  rugValues.push([r, 0.5]);
}

const yMin = Math.min(...ciLower) - 0.25;
const yMax = Math.max(...partialDependence.map((v, i) => v + halfWidth[i])) + 0.25;

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Title (scales down for long titles per style guide) --------------------
const titleText = "Crop Yield vs. Rainfall · pdp-basic · javascript · echarts · anyplot.ai";
const baseTitleFontSize = 22;
const titleFontSize =
  titleText.length > 67 ? Math.round((baseTitleFontSize * 67) / titleText.length) : baseTitleFontSize;

// --- Option -------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    data: ["Partial dependence", "Confidence interval", "Training data (rug)"],
    top: 70,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: [
    { left: 110, right: 60, top: 110, height: 560 },
    { left: 110, right: 60, top: 700, height: 70 },
  ],
  xAxis: [
    {
      gridIndex: 0,
      type: "value",
      min: R_MIN,
      max: R_MAX,
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    {
      gridIndex: 1,
      type: "value",
      min: R_MIN,
      max: R_MAX,
      name: "Rainfall (mm)",
      nameLocation: "middle",
      nameGap: 40,
      nameTextStyle: { color: t.ink, fontSize: 18 },
      axisLabel: { color: t.inkSoft, fontSize: 14 },
      axisLine: { lineStyle: { color: t.inkSoft } },
      axisTick: { lineStyle: { color: t.inkSoft } },
      splitLine: { show: false },
    },
  ],
  yAxis: [
    {
      gridIndex: 0,
      type: "value",
      min: Math.floor(yMin * 10) / 10,
      max: Math.ceil(yMax * 10) / 10,
      name: "Δ Predicted Yield (t/ha)",
      nameLocation: "middle",
      nameGap: 65,
      nameTextStyle: { color: t.ink, fontSize: 18 },
      axisLabel: {
        color: t.inkSoft,
        fontSize: 14,
        formatter: (v) => (v > 0 ? "+" : "") + v.toFixed(1),
      },
      axisLine: { lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      gridIndex: 1,
      type: "value",
      min: 0,
      max: 1,
      show: false,
      splitLine: { show: false },
    },
  ],
  series: [
    {
      name: "CI lower (hidden)",
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: ciLowerXY,
      stack: "confidence",
      symbol: "none",
      lineStyle: { opacity: 0 },
      areaStyle: { opacity: 0 },
      silent: true,
      legendHoverLink: false,
      z: 1,
    },
    {
      name: "Confidence interval",
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: ciBandHeightXY,
      stack: "confidence",
      symbol: "none",
      lineStyle: { opacity: 0 },
      areaStyle: { color: MUTED, opacity: 0.25 },
      itemStyle: { color: MUTED },
      silent: true,
      z: 1,
    },
    {
      name: "Partial dependence",
      type: "line",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: partialDependenceXY,
      symbol: "none",
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: { show: false },
        data: [{ yAxis: 0 }],
      },
      z: 3,
    },
    {
      name: "Training data (rug)",
      type: "scatter",
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: rugValues,
      symbol: "rect",
      symbolSize: [2, 24],
      itemStyle: { color: t.inkSoft, opacity: 0.5 },
    },
  ],
});
