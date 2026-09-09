// anyplot.ai
// timeline-basic: Event Timeline
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Product launch roadmap: milestones grouped by project phase.
const categories = ["Planning", "Development", "Testing", "Launch"];
const events = [
  { date: "2025-01-15", name: "Market Research Complete", category: "Planning" },
  { date: "2025-02-20", name: "Requirements Finalized", category: "Planning" },
  { date: "2025-03-24", name: "Design Sprint Wraps", category: "Planning" },
  { date: "2025-04-28", name: "Core API Built", category: "Development" },
  { date: "2025-06-09", name: "Beta Feature Freeze", category: "Development" },
  { date: "2025-07-14", name: "Internal Alpha Test", category: "Testing" },
  { date: "2025-08-25", name: "Public Beta Launch", category: "Testing" },
  { date: "2025-09-29", name: "Security Audit Passed", category: "Testing" },
  { date: "2025-11-03", name: "Marketing Campaign Starts", category: "Launch" },
  { date: "2025-12-10", name: "General Availability", category: "Launch" },
];

const DATE_LABEL = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const points = events.map((e, i) => ({
  timestamp: new Date(`${e.date}T00:00:00Z`).getTime(),
  name: e.name,
  category: e.category,
  dateLabel: DATE_LABEL.format(new Date(`${e.date}T00:00:00Z`)),
  side: i % 2 === 0 ? 1 : -1,
}));

const dayMs = 24 * 60 * 60 * 1000;
const minTime = Math.min(...points.map((p) => p.timestamp)) - 25 * dayMs;
const maxTime = Math.max(...points.map((p) => p.timestamp)) + 25 * dayMs;

// Vertical stems from the baseline (y=0) to each event marker, broken between
// events via a null-y point so ECharts starts a fresh segment per stem.
const stemData = [];
points.forEach((p) => {
  stemData.push([p.timestamp, 0]);
  stemData.push([p.timestamp, p.side]);
  stemData.push([p.timestamp, null]);
});

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
const titleText = "Product Launch Roadmap · timeline-basic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

const labelRich = {
  name: { color: t.ink, fontSize: 14, fontWeight: "bold", lineHeight: 20 },
  date: { color: t.inkSoft, fontSize: 12, lineHeight: 16 },
};

const categorySeries = categories.map((cat, i) => ({
  name: cat,
  type: "scatter",
  data: points
    .filter((p) => p.category === cat)
    .map((p) => ({
      value: [p.timestamp, p.side],
      name: p.name,
      dateLabel: p.dateLabel,
      label: {
        show: true,
        position: p.side > 0 ? "top" : "bottom",
        distance: 14,
        formatter: `{name|${p.name}}\n{date|${p.dateLabel}}`,
        rich: labelRich,
        align: "center",
      },
    })),
  symbolSize: 18,
  itemStyle: { color: t.palette[i], borderColor: t.pageBg, borderWidth: 2 },
  z: 3,
}));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    top: 40,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    data: categories,
    top: 100,
    left: "center",
    itemGap: 32,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  tooltip: {
    trigger: "item",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink },
    formatter: (params) =>
      `<b>${params.data.name}</b><br/>${params.seriesName} &middot; ${params.data.dateLabel}`,
  },
  grid: { left: 80, right: 80, top: 190, bottom: 190 },
  xAxis: {
    type: "time",
    min: minTime,
    max: maxTime,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{MMM} {yyyy}" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: -1.6,
    max: 1.6,
    show: false,
  },
  series: [
    {
      name: "baseline",
      type: "line",
      data: [
        [minTime, 0],
        [maxTime, 0],
      ],
      showSymbol: false,
      silent: true,
      lineStyle: { color: t.inkSoft, width: 2 },
      z: 1,
    },
    {
      name: "stems",
      type: "line",
      data: stemData,
      showSymbol: false,
      silent: true,
      connectNulls: false,
      lineStyle: { color: t.inkSoft, width: 1.5 },
      z: 2,
    },
    ...categorySeries,
  ],
});
