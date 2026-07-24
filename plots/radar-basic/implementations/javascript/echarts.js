// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-07-24
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Employee performance review across six competencies, comparing three roles.
const competencies = [
  "Communication",
  "Technical Skills",
  "Teamwork",
  "Leadership",
  "Problem Solving",
  "Time Management",
];

const reviews = [
  { name: "Junior Engineer", values: [65, 78, 82, 40, 70, 60] },
  { name: "Senior Engineer", values: [75, 92, 80, 65, 88, 78] },
  { name: "Engineering Manager", values: [90, 70, 85, 95, 75, 82] },
];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette.slice(0, reviews.length),
  backgroundColor: "transparent",
  title: {
    text: "radar-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: reviews.map((r) => r.name),
    bottom: 10,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 20,
    itemHeight: 12,
  },
  radar: {
    center: ["50%", "50%"],
    radius: "68%",
    splitNumber: 5,
    indicator: competencies.map((name) => ({ name, max: 100 })),
    name: { color: t.inkSoft, fontSize: 16 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    splitArea: { show: false },
  },
  series: [
    {
      type: "radar",
      data: reviews.map((r) => ({
        name: r.name,
        value: r.values,
        areaStyle: { opacity: 0.25 },
        lineStyle: { width: 3 },
        symbolSize: 8,
      })),
    },
  ],
});
