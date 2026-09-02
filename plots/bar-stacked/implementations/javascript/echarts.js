// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly software company revenue composition by product line ($K)
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const components = [
  { name: "Subscriptions", data: [20, 25, 30, 36, 42, 50] },
  { name: "Software", data: [58, 62, 65, 70, 74, 78] },
  { name: "Services", data: [30, 32, 35, 33, 38, 40] },
  { name: "Hardware", data: [42, 45, 40, 48, 44, 50] },
];
const totals = months.map((_, i) =>
  components.reduce((sum, c) => sum + c.data[i], 0)
);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Title (fontsize scaled to length; see plot-generator.md formula) -------
const titleText =
  "Quarterly SaaS Revenue by Product Line · bar-stacked · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    top: 70,
    data: components.map((c) => c.name),
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 90, right: 60, top: 130, bottom: 70 },
  xAxis: {
    type: "category",
    data: months,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Revenue ($K)",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...components.map((c) => ({
      name: c.name,
      type: "bar",
      stack: "revenue",
      barWidth: "55%",
      data: c.data,
    })),
    {
      name: "Total",
      type: "bar",
      stack: "revenue",
      data: months.map(() => 0),
      itemStyle: { color: "transparent" },
      label: {
        show: true,
        position: "top",
        color: t.ink,
        fontSize: 15,
        fontWeight: 500,
        formatter: (params) => totals[params.dataIndex],
      },
      tooltip: { show: false },
    },
  ],
});
