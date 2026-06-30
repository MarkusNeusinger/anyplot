// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-06-30
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Department efficiency scores (0–100) before/after digital transformation
// Sorted ascending by improvement so the largest gain appears at the top
const departments = [
  "Legal", "Finance", "Operations", "HR",
  "Logistics", "R&D", "Marketing", "IT", "Engineering", "Sales"
];
const scoreBefore = [74, 73, 70, 61, 69, 64, 55, 67, 62, 58];
const scoreAfter  = [80, 81, 85, 78, 86, 83, 79, 91, 88, 84];

const chart = echarts.init(document.getElementById("container"));

const titleText =
  "Digital Transformation · dumbbell-basic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: "500" }
  },
  legend: {
    data: [
      { name: "Before", icon: "circle", itemStyle: { color: t.palette[0] } },
      { name: "After",  icon: "circle", itemStyle: { color: t.palette[2] } }
    ],
    top: 58,
    left: "center",
    itemGap: 32,
    itemWidth: 14,
    itemHeight: 14,
    textStyle: { color: t.inkSoft, fontSize: 14 }
  },
  tooltip: {
    trigger: "item",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 13 },
    formatter: function(params) {
      if (params.seriesType !== "scatter") return "";
      const idx = params.dataIndex;
      const delta = scoreAfter[idx] - scoreBefore[idx];
      return (
        "<b>" + departments[idx] + "</b><br/>" +
        "Before: " + scoreBefore[idx] + "<br/>" +
        "After: "  + scoreAfter[idx]  + "<br/>" +
        "Change: +" + delta
      );
    }
  },
  grid: { left: 130, right: 60, top: 100, bottom: 70 },
  xAxis: {
    type: "value",
    min: 40,
    max: 100,
    name: "Efficiency Score",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } }
  },
  yAxis: {
    type: "category",
    data: departments,
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },
  series: [
    // Connector lines drawn via custom series (silent — excluded from legend)
    {
      type: "custom",
      name: "_connector",
      renderItem: function(params, api) {
        const s = api.coord([api.value(0), params.dataIndex]);
        const e = api.coord([api.value(1), params.dataIndex]);
        return {
          type: "line",
          shape: { x1: s[0], y1: s[1], x2: e[0], y2: e[1] },
          style: { stroke: t.inkSoft, lineWidth: 2.5, opacity: 0.4 }
        };
      },
      data: departments.map(function(_, i) { return [scoreBefore[i], scoreAfter[i]]; }),
      encode: { x: [0, 1] },
      z: 1,
      silent: true
    },
    // "Before" endpoints — Imprint palette position 1 (brand green)
    {
      type: "scatter",
      name: "Before",
      data: departments.map(function(d, i) { return [scoreBefore[i], d]; }),
      encode: { x: 0, y: 1 },
      symbolSize: 20,
      itemStyle: { color: t.palette[0] },
      z: 2
    },
    // "After" endpoints — Imprint palette position 3 (blue)
    {
      type: "scatter",
      name: "After",
      data: departments.map(function(d, i) { return [scoreAfter[i], d]; }),
      encode: { x: 0, y: 1 },
      symbolSize: 20,
      itemStyle: { color: t.palette[2] },
      z: 2
    }
  ]
});
