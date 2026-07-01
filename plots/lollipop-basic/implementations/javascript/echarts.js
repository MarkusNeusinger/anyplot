// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 88/100 | Created: 2026-07-01

const t = window.ANYPLOT_TOKENS;

// --- Data (average annual salary by profession, USD thousands) --------------
const professions = [
  "Software Eng.", "Data Scientist", "Physician",
  "Financial Analyst", "UX Designer", "Project Manager",
  "Mechanical Eng.", "Marketing Mgr.", "Nurse", "Teacher"
];
const salaries = [125, 118, 115, 95, 88, 85, 82, 75, 68, 58];
const avg = Math.round(salaries.reduce((a, b) => a + b, 0) / salaries.length);

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "lollipop-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 28,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" }
  },
  grid: { left: 90, right: 80, top: 90, bottom: 120 },
  xAxis: {
    type: "category",
    data: professions,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      rotate: 30,
      interval: 0
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false }
  },
  yAxis: {
    type: "value",
    name: "Avg. Annual Salary (USD thousands)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: 0,
    max: 150,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } }
  },
  series: [
    {
      type: "bar",
      data: salaries,
      barWidth: 2,
      itemStyle: { color: t.palette[0] },
      markLine: {
        symbol: "none",
        silent: true,
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: {
          position: "end",
          formatter: "Avg: " + avg + "K",
          color: t.inkSoft,
          fontSize: 13
        },
        data: [{ yAxis: avg, name: "Average" }]
      },
      z: 1
    },
    {
      type: "scatter",
      data: salaries,
      symbolSize: 16,
      itemStyle: { color: t.palette[0] },
      label: {
        show: true,
        position: "top",
        formatter: "{c}K",
        color: t.inkSoft,
        fontSize: 13
      },
      z: 2
    }
  ]
});
