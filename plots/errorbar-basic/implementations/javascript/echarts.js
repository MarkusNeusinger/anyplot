// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 86/100 | Created: 2026-06-30

const t = window.ANYPLOT_TOKENS;

// Data — wheat yield response to nitrogen fertilization (7 dose levels, n=5 field replicates)
const doses = ["0", "50", "100", "150", "200", "250", "300"];
const yieldMeans  = [2.1, 3.5, 4.8, 5.6, 5.9, 5.8, 5.4];
const yieldErrors = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

const errorBarData = yieldMeans.map(function(mean, i) {
  return [i, mean + yieldErrors[i], mean - yieldErrors[i]];
});
const scatterData = yieldMeans.map(function(mean, i) {
  return [i, mean];
});

// Init
const chart = echarts.init(document.getElementById("container"));

const BRAND = t.palette[0]; // #009E73 — Imprint palette position 1

// Option
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "errorbar-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 }
  },
  grid: { left: 120, right: 60, top: 90, bottom: 90 },
  xAxis: {
    type: "category",
    data: doses,
    name: "Nitrogen Dose (kg N/ha)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false }
  },
  yAxis: {
    type: "value",
    name: "Wheat Yield (t/ha)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: 0,
    max: 7,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } }
  },
  series: [
    {
      // Error bars drawn via custom renderer: vertical stem + top/bottom caps
      type: "custom",
      dimensions: ["xIdx", "yHigh", "yLow"],
      encode: { x: 0, y: [1, 2] },
      renderItem: function(params, api) {
        var xIdx  = api.value(0);
        var yHigh = api.value(1);
        var yLow  = api.value(2);
        var hiPt  = api.coord([xIdx, yHigh]);
        var loPt  = api.coord([xIdx, yLow]);
        var capHW = 20; // cap half-width in CSS px
        var lw    = 3;

        return {
          type: "group",
          children: [
            // Vertical stem
            {
              type: "line",
              shape: { x1: hiPt[0], y1: hiPt[1], x2: loPt[0], y2: loPt[1] },
              style: { stroke: BRAND, lineWidth: lw }
            },
            // Top cap
            {
              type: "line",
              shape: { x1: hiPt[0] - capHW, y1: hiPt[1], x2: hiPt[0] + capHW, y2: hiPt[1] },
              style: { stroke: BRAND, lineWidth: lw }
            },
            // Bottom cap
            {
              type: "line",
              shape: { x1: loPt[0] - capHW, y1: loPt[1], x2: loPt[0] + capHW, y2: loPt[1] },
              style: { stroke: BRAND, lineWidth: lw }
            }
          ]
        };
      },
      data: errorBarData,
      z: 3
    },
    {
      // Center-value markers overlaid on error bars
      type: "scatter",
      data: scatterData,
      symbolSize: 16,
      itemStyle: { color: BRAND, borderColor: t.pageBg, borderWidth: 2 },
      z: 4
    }
  ]
});
