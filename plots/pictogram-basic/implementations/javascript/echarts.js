// anyplot.ai
// pictogram-basic: Pictogram Chart (Isotype Visualization)
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-03

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Coffee production by country, 2022 (millions of 60 kg bags)
const ICON_UNIT  = 5;  // 1 icon = 5 million bags
const categories = ["Brazil", "Vietnam", "Colombia", "Indonesia", "Ethiopia", "Honduras"];
const production = [63, 29, 14, 12, 10, 8];
const iconCounts = production.map(v => v / ICON_UNIT);
const maxIcons   = 14;  // axis ceiling (above max 12.6)

// Scale title font for longer string
const titleText = "Coffee Production · pictogram-basic · javascript · echarts · anyplot.ai";
const titleSize = Math.max(14, Math.round(22 * 67 / titleText.length));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: titleText,
    subtext: "○  Each icon = 5 million 60 kg bags",
    left: "center",
    top: 20,
    textStyle: {
      color: t.ink,
      fontSize: titleSize,
      fontWeight: "bold",
    },
    subtextStyle: {
      color: t.inkSoft,
      fontSize: 16,
    },
    itemGap: 8,
  },

  grid: {
    left: 130,
    right: 160,
    top: 130,
    bottom: 90,
  },

  xAxis: {
    type: "value",
    max: maxIcons,
    interval: 2,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: v => v > 0 ? (v * ICON_UNIT) + "M" : "0",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
    name: "Production (millions of 60 kg bags)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
  },

  yAxis: {
    type: "category",
    data: categories,
    inverse: true,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 16,
      margin: 12,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  series: [
    {
      type: "pictorialBar",
      symbol: "circle",
      symbolSize: [80, 80],
      symbolMargin: "10%",
      symbolRepeat: true,
      symbolBoundingData: maxIcons,
      emphasis: { disabled: true },
      label: {
        show: true,
        position: "right",
        color: t.inkSoft,
        fontSize: 14,
        formatter: params => production[params.dataIndex] + "M bags",
      },
      data: iconCounts.map((val, i) => ({
        value: val,
        itemStyle: { color: t.palette[i % 8] },
      })),
    },
  ],
});
