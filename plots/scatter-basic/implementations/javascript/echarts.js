// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 84/100 | Created: 2026-06-02

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) -----------------------------------
// Health study: height (cm) vs weight (kg), 120 participants, r ≈ 0.7
let seed = 42;
const rng = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
const randn = () => {
  const u = rng() + 1e-10;
  const v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
};

const n = 120;
const heightMean = 170, heightStd = 10;
const weightMean = 70, weightStd = 12, r = 0.7;
const points = [];
for (let i = 0; i < n; i++) {
  const h = heightMean + randn() * heightStd;
  const noise = randn() * weightStd * Math.sqrt(1 - r * r);
  const w = weightMean + r * (weightStd / heightStd) * (h - heightMean) + noise;
  points.push([+h.toFixed(1), +w.toFixed(1)]);
}

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "scatter-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
  },
  grid: { left: 110, right: 60, top: 90, bottom: 90 },
  xAxis: {
    type: "value",
    min: 140,
    max: 205,
    name: "Height (cm)",
    nameLocation: "middle",
    nameGap: 52,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    min: 35,
    max: 100,
    name: "Weight (kg)",
    nameLocation: "middle",
    nameRotate: 90,
    nameGap: 72,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "scatter",
      data: points,
      symbolSize: 12,
      itemStyle: {
        color: t.palette[0],
        opacity: 0.7,
        borderColor: t.pageBg,
        borderWidth: 1,
      },
    },
  ],
});
