// anyplot.ai
// box-grouped: Grouped Box Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simple LCG + Box-Muller so the sample data is reproducible without Math.random().
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function quantile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

function boxStats(values) {
  const sorted = values.slice().sort((a, b) => a - b);
  const q1 = quantile(sorted, 0.25);
  const median = quantile(sorted, 0.5);
  const q3 = quantile(sorted, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const inliers = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  const outliers = sorted.filter((v) => v < lowerFence || v > upperFence);
  return {
    whiskerLow: inliers.length ? inliers[0] : q1,
    q1,
    median,
    q3,
    whiskerHigh: inliers.length ? inliers[inliers.length - 1] : q3,
    outliers,
  };
}

const N_SAMPLES = 45;
const departments = ["Engineering", "Sales", "Marketing", "Support"];
const levels = ["Junior", "Mid", "Senior"];
const levelBaseline = { Junior: 60, Mid: 73, Senior: 84 };
const levelSpread = { Junior: 16, Mid: 11, Senior: 6 };
const deptOffset = { Engineering: 4, Sales: -3, Marketing: 1, Support: -6 };
const middleLevelIndex = Math.floor((levels.length - 1) / 2);

const categories = [];
const boxItems = [];
const outlierItems = [];

departments.forEach((dept, i) => {
  levels.forEach((level, j) => {
    const samples = [];
    for (let k = 0; k < N_SAMPLES; k++) {
      const raw = randNormal(
        levelBaseline[level] + deptOffset[dept],
        levelSpread[level],
      );
      samples.push(Math.min(100, Math.max(0, raw)));
    }
    const stats = boxStats(samples);
    const catIndex = categories.length;
    categories.push(j === middleLevelIndex ? dept : "");
    boxItems.push({
      value: [
        stats.whiskerLow,
        stats.q1,
        stats.median,
        stats.q3,
        stats.whiskerHigh,
      ],
      itemStyle: {
        color: t.elevatedBg,
        borderColor: t.palette[j],
        borderWidth: 2.5,
      },
    });
    stats.outliers.forEach((v) => {
      outlierItems.push({
        value: [catIndex, v],
        itemStyle: {
          color: t.palette[j],
          borderColor: t.pageBg,
          borderWidth: 1,
        },
      });
    });
  });
  // Gap tick between department groups so the side-by-side boxes read as clusters.
  // NaN values (rather than a bare null item) keep echarts' box-plot data
  // preprocessing happy while still making data.hasValue() skip the render.
  if (i < departments.length - 1) {
    categories.push("");
    boxItems.push({ value: [NaN, NaN, NaN, NaN, NaN] });
  }
});

const title = "box-grouped · javascript · echarts · anyplot.ai";

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 26,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: levels,
    top: 74,
    itemWidth: 18,
    itemHeight: 14,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  tooltip: { trigger: "item" },
  grid: { left: 130, right: 70, top: 140, bottom: 90 },
  xAxis: {
    type: "category",
    data: categories,
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 0 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Performance Score",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 100,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...levels.map((level, j) => ({
      name: level,
      type: "scatter",
      data: [],
      symbol: "rect",
      symbolSize: [16, 14],
      itemStyle: { color: t.palette[j] },
    })),
    {
      name: "Distribution",
      type: "boxplot",
      data: boxItems,
      boxWidth: ["45%", "68%"],
    },
    {
      name: "Outliers",
      type: "scatter",
      data: outlierItems,
      symbolSize: 12,
      z: 3,
    },
  ],
});
