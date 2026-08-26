// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
const quarters = ["2023 Q1", "2023 Q2", "2023 Q3", "2023 Q4", "2024 Q1", "2024 Q2"];
const services = ["Compute", "Storage", "Networking", "Database"];
const spendByService = {
  Compute: [180, 195, 210, 225, 240, 258],
  Storage: [90, 95, 102, 110, 118, 125],
  Networking: [45, 48, 52, 58, 62, 67],
  Database: [65, 70, 75, 82, 88, 95],
};
const totals = quarters.map((_, i) =>
  services.reduce((sum, service) => sum + spendByService[service][i], 0)
);
const yAxisMax = Math.ceil((Math.max(...totals) * 1.15) / 50) * 50;

const title = "Cloud Spend by Service · bar-stacked-labeled · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    data: services,
    top: 76,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 18,
    itemHeight: 14,
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    valueFormatter: (value) => `$${value}K`,
  },
  grid: { left: 110, right: 60, top: 150, bottom: 70, containLabel: false },
  xAxis: {
    type: "category",
    data: quarters,
    axisLabel: { color: t.inkSoft, fontSize: 16 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Spend ($K)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    max: yAxisMax,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...services.map((service) => ({
      name: service,
      type: "bar",
      stack: "spend",
      barWidth: "56%",
      data: spendByService[service],
    })),
    {
      name: "Total",
      type: "bar",
      stack: "spend",
      data: totals.map(() => 0),
      itemStyle: { color: "transparent" },
      silent: true,
      tooltip: { show: false },
      label: {
        show: true,
        position: "top",
        distance: 14,
        color: t.ink,
        fontSize: 19,
        fontWeight: "bold",
        formatter: (params) => `$${totals[params.dataIndex]}K`,
      },
    },
  ],
});
