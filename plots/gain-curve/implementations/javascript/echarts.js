// anyplot.ai
// gain-curve: Cumulative Gains Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) -----------------------------------------
// Fixed-seed LCG — the browser has no seeded RNG.
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

// Simulated churn-prediction model: 2000 customers, ~18% actually churned.
// The model score correlates with the true outcome but overlaps realistically.
const sampleCount = 2000;
const churnRate = 0.18;
const customers = [];
for (let i = 0; i < sampleCount; i++) {
  const churned = rand() < churnRate ? 1 : 0;
  const score = churned
    ? 0.35 + 0.65 * rand()
    : 0.05 + 0.55 * rand();
  customers.push({ churned, score });
}

customers.sort((a, b) => b.score - a.score);

const totalPositives = customers.reduce((sum, c) => sum + c.churned, 0);
const modelCurve = [[0, 0]];
let capturedPositives = 0;
for (let i = 0; i < customers.length; i++) {
  capturedPositives += customers[i].churned;
  const targetedPct = ((i + 1) / sampleCount) * 100;
  const capturedPct = (capturedPositives / totalPositives) * 100;
  modelCurve.push([targetedPct, capturedPct]);
}

const baselineCurve = [
  [0, 0],
  [100, 100],
];

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "gain-curve · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: ["Model", "Random selection"],
    top: 70,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 90, right: 60, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Percentage of customers targeted",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 100,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Cumulative churners captured",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 100,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Random selection",
      type: "line",
      data: baselineCurve,
      symbol: "none",
      color: t.ink,
      lineStyle: { color: t.ink, width: 2, type: "dashed" },
      z: 1,
    },
    {
      name: "Model",
      type: "line",
      data: modelCurve,
      symbol: "none",
      color: t.palette[0],
      lineStyle: { color: t.palette[0], width: 3.5 },
      z: 2,
    },
  ],
});
