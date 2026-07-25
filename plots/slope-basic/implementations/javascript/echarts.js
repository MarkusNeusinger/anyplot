// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-07-25

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Employee engagement survey score (0-100) by department, before vs after a
// company-wide feedback program.
const departments = [
  { name: "Product", start: 82, end: 88 },
  { name: "HR", start: 80, end: 83 },
  { name: "Marketing", start: 75, end: 70 },
  { name: "Finance", start: 77, end: 72 },
  { name: "Design", start: 73, end: 77 },
  { name: "Engineering", start: 72, end: 81 },
  { name: "Sales", start: 68, end: 74 },
  { name: "Operations", start: 70, end: 68 },
  { name: "Support", start: 64, end: 79 },
  { name: "Legal", start: 66, end: 65 },
];

const INCREASE = t.palette[0]; // "#009E73" brand green — profit/up/gain
const DECREASE = t.palette[4]; // "#AE3030" matte red — semantic anchor for loss/down

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
const title = "Employee Engagement Score · slope-basic · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  grid: { left: 300, right: 300, top: 130, bottom: 90 },
  xAxis: {
    type: "category",
    data: ["2024 (before)", "2025 (after)"],
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 16 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 62,
    max: 90,
    show: false,
  },
  series: departments.map((d) => {
    const color = d.end >= d.start ? INCREASE : DECREASE;
    return {
      name: d.name,
      type: "line",
      symbol: "circle",
      symbolSize: 8,
      lineStyle: { width: 3, color },
      itemStyle: { color },
      data: [
        {
          value: d.start,
          label: {
            show: true,
            position: "left",
            distance: 16,
            formatter: () => `${d.name}  ${d.start}`,
            color: t.ink,
            fontSize: 14,
          },
        },
        {
          value: d.end,
          label: {
            show: true,
            position: "right",
            distance: 16,
            formatter: () => `${d.end}  ${d.name}`,
            color: t.ink,
            fontSize: 14,
          },
        },
      ],
    };
  }),
});
