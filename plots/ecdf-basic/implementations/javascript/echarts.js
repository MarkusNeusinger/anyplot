// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 90/100 | Created: 2026-06-25

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Seeded LCG for reproducible in-browser data generation (no Math.random())
function lcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

// Box-Muller transform for normal distribution samples
function normalSamples(n, mean, std, rng) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const u1 = Math.max(rng(), 1e-10);
    const u2 = rng();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    out.push(mean + std * z);
  }
  return out;
}

// Data: exam scores for two student groups in a university statistics course
const rng = lcg(42);
const tutoringScores  = normalSamples(200, 75, 12, rng);  // weekly tutoring sessions
const selfStudyScores = normalSamples(200, 63, 15, rng);  // independent study only

// Build ECDF: sort and pair each value with its cumulative proportion
const tSorted = [...tutoringScores].sort((a, b) => a - b);
const sSorted = [...selfStudyScores].sort((a, b) => a - b);

const toECDF = (s) => {
  const n = s.length, pad = (s[n - 1] - s[0]) * 0.03;
  return [[+(s[0] - pad).toFixed(2), 0], ...s.map((x, i) => [+x.toFixed(2), +((i + 1) / n).toFixed(4)])];
};

const tPts    = toECDF(tSorted);
const sPts    = toECDF(sSorted);
const tMedian = +tSorted[Math.floor(tSorted.length / 2)].toFixed(1);
const sMedian = +sSorted[Math.floor(sSorted.length / 2)].toFixed(1);

// Chart
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "ecdf-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },
  legend: {
    data: ["Tutoring (n=200)", "Self-Study (n=200)"],
    right: 80,
    top: 62,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    itemWidth: 28,
    itemHeight: 3,
    backgroundColor: t.elevatedBg,
    borderRadius: 4,
    padding: [8, 14],
  },
  tooltip: {
    trigger: "axis",
    formatter: (params) => {
      const score = params[0].value[0].toFixed(1);
      return `Score: ${score}<br/>` +
        params.map(p => `${p.seriesName}: ${(p.value[1] * 100).toFixed(1)}%`).join("<br/>");
    },
  },
  grid: { left: 100, right: 80, top: 110, bottom: 85 },
  xAxis: {
    type: "value",
    name: "Exam Score",
    nameLocation: "center",
    nameGap: 48,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
    min: 15,
    max: 120,
  },
  yAxis: {
    type: "value",
    name: "Cumulative Proportion",
    nameLocation: "center",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => v.toFixed(1) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
    min: 0,
    max: 1,
  },
  series: [
    {
      name: "Tutoring (n=200)",
      type: "line",
      step: "end",
      data: tPts,
      lineStyle: { color: t.palette[0], width: 3 },
      itemStyle: { color: t.palette[0] },
      areaStyle: { color: t.palette[0], opacity: 0.12 },
      showSymbol: false,
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.palette[0], type: "dashed", opacity: 0.55, width: 1.5 },
        label: { formatter: `Median ${tMedian}`, color: t.inkSoft, fontSize: 12, position: "end" },
        data: [{ xAxis: tMedian }],
      },
    },
    {
      name: "Self-Study (n=200)",
      type: "line",
      step: "end",
      data: sPts,
      lineStyle: { color: t.palette[1], width: 3, type: "dashed" },
      itemStyle: { color: t.palette[1] },
      areaStyle: { color: t.palette[1], opacity: 0.10 },
      showSymbol: false,
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.palette[1], type: "dashed", opacity: 0.55, width: 1.5 },
        label: { formatter: `Median ${sMedian}`, color: t.inkSoft, fontSize: 12, position: "end" },
        data: [{ xAxis: sMedian }],
      },
    },
  ],
});
