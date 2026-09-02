// anyplot.ai
// cat-box-strip: Box Plot with Strip Overlay
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + Box-Muller gaussian -------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian(mean, std) {
  const u1 = Math.max(lcg(), 1e-12);
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

// --- Box-plot summary stats (Tukey whiskers, 1.5x IQR fence) ---------------
function boxStats(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const quantile = (p) => {
    const pos = (sorted.length - 1) * p;
    const lo = Math.floor(pos);
    const hi = Math.ceil(pos);
    return lo === hi
      ? sorted[lo]
      : sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
  };
  const q1 = quantile(0.25);
  const median = quantile(0.5);
  const q3 = quantile(0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const withinFence = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  const whiskerMin = withinFence.length ? withinFence[0] : sorted[0];
  const whiskerMax = withinFence.length
    ? withinFence[withinFence.length - 1]
    : sorted[sorted.length - 1];
  return [whiskerMin, q1, median, q3, whiskerMax];
}

// --- Data: marathon finish times (minutes) by runner age group -------------
const ageGroups = ["20-29", "30-39", "40-49", "50-59", "60+"];
const meansByGroup = [245, 252, 268, 288, 315];
const stdsByGroup = [28, 30, 32, 34, 36];
const countsByGroup = [58, 65, 62, 45, 34];

const rawByGroup = ageGroups.map((_, i) => {
  const values = [];
  for (let j = 0; j < countsByGroup[i]; j++) {
    values.push(Math.max(150, gaussian(meansByGroup[i], stdsByGroup[i])));
  }
  return values;
});

const boxData = rawByGroup.map(boxStats);
const medians = boxData.map((d) => d[2]);
const medianDelta = Math.round(medians[medians.length - 1] - medians[0]);

// Strip overlay: every individual runner, jittered around its category slot
const stripPoints = [];
rawByGroup.forEach((values, catIndex) => {
  values.forEach((v) => {
    const jitter = (lcg() - 0.5) * 0.72;
    stripPoints.push([catIndex + jitter, v]);
  });
});

// --- Init --------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "cat-box-strip · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Distribution", "Runners"],
    top: 50,
    textStyle: { color: t.inkSoft, fontSize: 14 },
  },
  grid: { left: 100, right: 60, top: 110, bottom: 90 },
  xAxis: {
    type: "category",
    data: ageGroups,
    name: "Runner Age Group",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    scale: true,
    name: "Finish Time (minutes)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Distribution",
      type: "boxplot",
      data: boxData,
      boxWidth: [20, 40],
      itemStyle: {
        color: "transparent",
        borderColor: t.palette[0],
        borderWidth: 2.5,
      },
      markLine: {
        silent: true,
        symbol: ["none", "none"],
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: {
          show: true,
          color: t.inkSoft,
          fontSize: 12,
          position: "middle",
          formatter: `Median +${medianDelta} min (20-29 → 60+)`,
        },
        data: [
          [
            { coord: [ageGroups[0], medians[0]] },
            { coord: [ageGroups[ageGroups.length - 1], medians[medians.length - 1]] },
          ],
        ],
      },
      z: 2,
    },
    {
      name: "Runners",
      type: "scatter",
      data: stripPoints,
      symbolSize: 7,
      itemStyle: { color: t.palette[0], opacity: 0.4 },
      z: 3,
      silent: true,
    },
  ],
});
