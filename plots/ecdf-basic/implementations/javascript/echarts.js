// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 84/100 | Created: 2026-06-25

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

// Build ECDF as [x, cumulative_proportion] pairs; prepend a leading zero point
function ecdf(data) {
  const sorted = [...data].sort((a, b) => a - b);
  const n = sorted.length;
  const pad = (sorted[n - 1] - sorted[0]) * 0.03;
  const start = [[+(sorted[0] - pad).toFixed(2), 0]];
  const pts = sorted.map((x, i) => [+x.toFixed(2), +((i + 1) / n).toFixed(4)]);
  return start.concat(pts);
}

// Data: exam scores for two student groups in a university statistics course
const rng = lcg(42);
const tutoringScores  = normalSamples(200, 75, 12, rng);  // weekly tutoring sessions
const selfStudyScores = normalSamples(200, 63, 15, rng);  // independent study only

const ecdfTutoring  = ecdf(tutoringScores);
const ecdfSelfStudy = ecdf(selfStudyScores);

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
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
  },
  legend: {
    data: ["Tutoring (n=200)", "Self-Study (n=200)"],
    right: 80,
    top: 62,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    itemWidth: 28,
    itemHeight: 3,
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
    axisTick: { lineStyle: { color: t.inkSoft } },
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
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    min: 0,
    max: 1,
  },
  series: [
    {
      name: "Tutoring (n=200)",
      type: "line",
      step: "end",
      data: ecdfTutoring,
      lineStyle: { color: t.palette[0], width: 3 },
      itemStyle: { color: t.palette[0] },
      showSymbol: false,
    },
    {
      name: "Self-Study (n=200)",
      type: "line",
      step: "end",
      data: ecdfSelfStudy,
      lineStyle: { color: t.palette[1], width: 3 },
      itemStyle: { color: t.palette[1] },
      showSymbol: false,
    },
  ],
});
