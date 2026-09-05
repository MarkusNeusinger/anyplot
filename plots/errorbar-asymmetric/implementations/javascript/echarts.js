// anyplot.ai
// errorbar-asymmetric: Asymmetric Error Bars Plot
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Quarterly revenue-growth forecast: downside risk shrinks while upside
// potential grows across the forecast horizon (planned product launches),
// producing genuinely asymmetric 10th-90th percentile bounds per quarter.
const quarters = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"];
const forecast = [3.2, 4.1, 2.8, 5.5, 4.7, 6.0];
const errorLower = [1.5, 2.0, 3.2, 1.8, 2.5, 3.0];
const errorUpper = [0.8, 1.0, 1.2, 2.5, 3.5, 4.0];

const lowerBound = forecast.map((y, i) => y - errorLower[i]);
const upperBound = forecast.map((y, i) => y + errorUpper[i]);
const rangeData = quarters.map((_, i) => [i, lowerBound[i], upperBound[i]]);

const brand = t.palette[0];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Render item for the asymmetric whisker (vertical line + end caps) -----
function renderErrorBar(params, api) {
  const xValue = api.value(0);
  const lowPoint = api.coord([xValue, api.value(1)]);
  const highPoint = api.coord([xValue, api.value(2)]);
  const halfWidth = api.size([1, 0])[0] * 0.15;
  const style = { stroke: brand, lineWidth: 3, lineCap: "round" };

  return {
    type: "group",
    children: [
      {
        type: "line",
        shape: { x1: lowPoint[0], y1: lowPoint[1], x2: highPoint[0], y2: highPoint[1] },
        style,
      },
      {
        type: "line",
        shape: {
          x1: lowPoint[0] - halfWidth,
          y1: lowPoint[1],
          x2: lowPoint[0] + halfWidth,
          y2: lowPoint[1],
        },
        style,
      },
      {
        type: "line",
        shape: {
          x1: highPoint[0] - halfWidth,
          y1: highPoint[1],
          x2: highPoint[0] + halfWidth,
          y2: highPoint[1],
        },
        style,
      },
    ],
  };
}

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "errorbar-asymmetric · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    top: 56,
    data: ["10th-90th percentile range", "Point forecast"],
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },
  grid: { left: 90, right: 60, top: 150, bottom: 80 },
  xAxis: {
    type: "category",
    data: quarters,
    name: "Forecast quarter",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Revenue growth (%)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "10th-90th percentile range",
      type: "custom",
      renderItem: renderErrorBar,
      itemStyle: { color: brand },
      encode: { x: 0, y: [1, 2] },
      data: rangeData,
      z: 2,
    },
    {
      name: "Point forecast",
      type: "scatter",
      data: forecast,
      symbolSize: 20,
      itemStyle: { color: brand, borderColor: t.pageBg, borderWidth: 3 },
      z: 3,
    },
  ],
});
