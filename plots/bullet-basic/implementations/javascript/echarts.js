// anyplot.ai
// bullet-basic: Basic Bullet Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-24
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly KPI dashboard — every metric normalised to "% of target achieved"
// so the four bullets share one common scale, as recommended for comparison.
const labels = ["Revenue Growth", "Customer Retention", "NPS Score", "On-Time Delivery"];
const actual = [82, 91, 68, 95];
const target = [90, 85, 75, 90];
const ranges = [50, 75, 100]; // poor / satisfactory / good thresholds, shared by all rows

const bandPoor = labels.map(() => ranges[0]);
const bandSatisfactory = labels.map(() => ranges[1] - ranges[0]);
const bandGood = labels.map(() => ranges[2] - ranges[1]);
const targetPoints = target.map((value, index) => [value, index]);

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Quarterly KPI Dashboard · bullet-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  legend: {
    top: 68,
    left: "center",
    data: ["Poor", "Satisfactory", "Good", "Actual", "Target"],
    itemWidth: 14,
    itemHeight: 14,
    textStyle: { color: t.inkSoft, fontSize: 14 },
  },
  grid: { left: 200, right: 90, top: 150, bottom: 80 },
  xAxis: {
    type: "value",
    min: 0,
    max: 100,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: labels,
    inverse: true,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      name: "Poor",
      type: "bar",
      stack: "range",
      barWidth: "55%",
      silent: true,
      data: bandPoor,
      itemStyle: { color: t.ink, opacity: 0.22 },
      z: 1,
    },
    {
      name: "Satisfactory",
      type: "bar",
      stack: "range",
      barWidth: "55%",
      silent: true,
      data: bandSatisfactory,
      itemStyle: { color: t.ink, opacity: 0.13 },
      z: 1,
    },
    {
      name: "Good",
      type: "bar",
      stack: "range",
      barWidth: "55%",
      silent: true,
      data: bandGood,
      itemStyle: { color: t.ink, opacity: 0.06 },
      z: 1,
    },
    {
      name: "Actual",
      type: "bar",
      barWidth: "22%",
      barGap: "-100%",
      data: actual,
      itemStyle: { color: t.palette[0] },
      label: {
        show: true,
        position: "right",
        color: t.ink,
        fontSize: 14,
        formatter: (p) => `${p.value}%`,
      },
      z: 2,
    },
    {
      name: "Target",
      type: "scatter",
      symbol: "rect",
      symbolSize: [6, 105],
      data: targetPoints,
      itemStyle: { color: t.ink },
      z: 3,
    },
  ],
});
