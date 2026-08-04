// anyplot.ai
// waterfall-basic: Basic Waterfall Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-08-04

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly bridge from starting revenue to net profit, in $ thousands.
const categories = [
  "Starting Revenue",
  "Product Sales",
  "Service Revenue",
  "Returns & Discounts",
  "Operating Costs",
  "Taxes",
  "Net Profit",
];
const stepType = ["total", "increase", "increase", "decrease", "decrease", "decrease", "total"];
const rawValues = [850, 320, 180, -95, -410, -145, 700];

const base = [];
const totalSeries = [];
const increaseSeries = [];
const decreaseSeries = [];
const connectorTop = [];
const labelText = [];

let cumulative = 0;
for (let i = 0; i < categories.length; i++) {
  const kind = stepType[i];
  const value = rawValues[i];

  totalSeries.push(0);
  increaseSeries.push(0);
  decreaseSeries.push(0);

  if (kind === "total") {
    base.push(0);
    totalSeries[i] = value;
    cumulative = value;
    labelText.push(`$${value}k`);
  } else if (kind === "increase") {
    base.push(cumulative);
    increaseSeries[i] = value;
    cumulative += value;
    labelText.push(`+$${value}k`);
  } else {
    cumulative += value;
    base.push(cumulative);
    decreaseSeries[i] = -value;
    labelText.push(`-$${Math.abs(value)}k`);
  }
  connectorTop.push(cumulative);
}

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const topLabel = {
  show: true,
  position: "top",
  color: t.inkSoft,
  fontSize: 14,
  formatter: (params) => (params.value === 0 ? "" : labelText[params.dataIndex]),
};

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "waterfall-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Total", "Increase", "Decrease"],
    top: 60,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 16,
    itemHeight: 12,
  },
  grid: { left: 110, right: 60, top: 130, bottom: 90 },
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
    name: "Amount ($ thousands)",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "${value}k" },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "placeholder",
      type: "bar",
      stack: "total",
      silent: true,
      itemStyle: { color: "transparent" },
      data: base,
    },
    {
      name: "Total",
      type: "bar",
      stack: "total",
      barWidth: "55%",
      itemStyle: { color: t.palette[2] },
      label: topLabel,
      data: totalSeries,
    },
    {
      name: "Increase",
      type: "bar",
      stack: "total",
      barWidth: "55%",
      itemStyle: { color: t.palette[0] },
      label: topLabel,
      data: increaseSeries,
    },
    {
      name: "Decrease",
      type: "bar",
      stack: "total",
      barWidth: "55%",
      itemStyle: { color: t.palette[4] },
      label: topLabel,
      data: decreaseSeries,
    },
    {
      name: "connector",
      type: "line",
      step: "end",
      symbol: "none",
      silent: true,
      legendHoverLink: false,
      lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5, opacity: 0.6 },
      data: connectorTop,
    },
  ],
});
