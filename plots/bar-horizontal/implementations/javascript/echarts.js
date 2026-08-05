// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Survey: reasons customers cited for choosing a software subscription (n=500,
// multi-select, so shares don't sum to 100). Sorted descending for ranking.
const reasons = [
  "Ease of use and onboarding",
  "Price and value for money",
  "Customer support quality",
  "Integration with existing tools",
  "Feature completeness",
  "Data security and compliance",
  "Recommendation from a colleague",
  "Brand reputation",
];
const shares = [68, 61, 54, 47, 41, 35, 24, 18];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bar-horizontal · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 24, right: 90, top: 100, bottom: 70, containLabel: true },
  xAxis: {
    type: "value",
    name: "Respondents citing this reason (%)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    max: 80,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: reasons,
    inverse: true,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "bar",
      data: shares,
      barCategoryGap: "35%",
      itemStyle: { color: t.palette[0], borderRadius: [0, 4, 4, 0] },
      label: {
        show: true,
        position: "right",
        formatter: "{c}%",
        color: t.ink,
        fontSize: 14,
      },
    },
  ],
});
