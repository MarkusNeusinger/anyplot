// anyplot.ai
// box-horizontal: Horizontal Box Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Annual salary distributions by job title — long category labels are exactly
// where the horizontal orientation earns its keep (no rotated x-axis text).
function makeLcg(seed) {
  let state = seed % 2147483647;
  if (state <= 0) state += 2147483646;
  return function uniform() {
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
}
const rand = makeLcg(42);

function randNormal(mean, std) {
  const u1 = rand();
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

function percentile(sorted, p) {
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

const roles = [
  {
    name: "Customer Support Representative",
    n: 20,
    mean: 48,
    std: 6,
    extra: [],
  },
  { name: "Marketing Specialist", n: 18, mean: 62, std: 9, extra: [] },
  { name: "UX Researcher", n: 16, mean: 88, std: 11, extra: [42] },
  { name: "Data Scientist", n: 17, mean: 118, std: 15, extra: [] },
  { name: "Product Manager", n: 18, mean: 125, std: 18, extra: [72] },
  { name: "Software Engineer", n: 22, mean: 132, std: 20, extra: [214] },
];

// Sort by median ascending so the axis reads low-to-high bottom-to-top —
// per the spec's "sort by median for easier comparison" guidance.
const withScores = roles.map((role) => {
  const salaries = [];
  for (let i = 0; i < role.n; i++) {
    salaries.push(
      Math.round(Math.max(28, randNormal(role.mean, role.std)) * 10) / 10,
    );
  }
  role.extra.forEach((v) => salaries.push(v));
  salaries.sort((a, b) => a - b);
  return { name: role.name, salaries, median: percentile(salaries, 0.5) };
});
withScores.sort((a, b) => a.median - b.median);

const categoryNames = withScores.map((r) => r.name);
const boxData = [];
const outlierData = [];

withScores.forEach((role, catIndex) => {
  const salaries = role.salaries;
  const q1 = percentile(salaries, 0.25);
  const median = percentile(salaries, 0.5);
  const q3 = percentile(salaries, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;

  const inliers = salaries.filter((v) => v >= lowerFence && v <= upperFence);
  const outliers = salaries.filter((v) => v < lowerFence || v > upperFence);

  const color = t.palette[catIndex];
  boxData.push({
    value: [inliers[0], q1, median, q3, inliers[inliers.length - 1]],
    itemStyle: { color: t.elevatedBg, borderColor: color, borderWidth: 3 },
  });
  outliers.forEach((v) => {
    outlierData.push({
      value: [v, catIndex],
      itemStyle: {
        color: color,
        opacity: 0.85,
        borderColor: t.pageBg,
        borderWidth: 1,
      },
    });
  });
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "box-horizontal · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 24, fontWeight: 500 },
  },
  grid: { left: 40, right: 70, top: 100, bottom: 90, containLabel: true },
  xAxis: {
    type: "value",
    name: "Annual Salary ($1,000s)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: categoryNames,
    boundaryGap: true,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      name: "Salary distribution",
      type: "boxplot",
      data: boxData,
      boxWidth: [16, 32],
    },
    {
      name: "Outliers",
      type: "scatter",
      data: outlierData,
      symbolSize: 13,
    },
  ],
});
