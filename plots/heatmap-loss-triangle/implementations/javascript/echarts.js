//# anyplot-orientation: square

// anyplot.ai
// heatmap-loss-triangle: Actuarial Loss Development Triangle
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;

// --- Data -------------------------------------------------------------------
// General liability insurance portfolio
// 10 accident years (2015–2024) × 10 development periods

const accidentYears = ["2015","2016","2017","2018","2019","2020","2021","2022","2023","2024"];
const devPeriods = ["1","2","3","4","5","6","7","8","9","10"];

// Cumulative paid claims as % of ultimate (typical general liability development pattern)
const pctPaid = [0.28, 0.45, 0.62, 0.74, 0.83, 0.90, 0.95, 0.98, 0.99, 1.00];

// Ultimate loss estimates by accident year ($M) — deterministic
const ultimates = [45.2, 52.8, 38.6, 61.3, 48.9, 55.1, 42.7, 67.4, 51.3, 59.8];

// Age-to-age link ratio factors between consecutive development periods
const ataFactors = pctPaid.slice(1).map((v, i) => (v / pctPaid[i]).toFixed(3));

// Triangle boundary: accident year i (0=2015) has actual data for periods j <= (9-i)
const actualData = [];
const projectedData = [];
let actualMin = Infinity, actualMax = 0;

for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 10; j++) {
    const value = +(ultimates[i] * pctPaid[j]).toFixed(1);
    if (j <= 9 - i) {
      actualData.push([j, i, value]);
      if (value < actualMin) actualMin = value;
      if (value > actualMax) actualMax = value;
    } else {
      projectedData.push([j, i, value]);
    }
  }
}

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: "heatmap-loss-triangle · javascript · echarts · anyplot.ai",
    subtext: "General Liability · Cumulative Paid Claims ($M) · Accident Years 2015–2024",
    left: "center",
    top: 22,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
    subtextStyle: { color: t.inkSoft, fontSize: 15 }
  },

  grid: {
    left: 90,
    right: 132,
    top: 148,
    bottom: 145
  },

  xAxis: {
    type: "category",
    data: devPeriods,
    name: "Development Period (Years)",
    nameLocation: "middle",
    nameGap: 68,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      interval: 0,
      lineHeight: 22,
      formatter: (value, index) =>
        index > 0 ? `${value}\n×${ataFactors[index - 1]}` : `${value}\n`
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },

  yAxis: {
    type: "category",
    data: accidentYears,
    name: "Accident Year",
    nameLocation: "middle",
    nameGap: 58,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
    inverse: true
  },

  visualMap: {
    min: actualMin,
    max: actualMax,
    seriesIndex: [0],
    show: true,
    orient: "vertical",
    right: 12,
    top: "middle",
    itemHeight: 200,
    itemWidth: 14,
    inRange: { color: t.seq || ["#009E73", "#4467A3"] },
    text: [
      "$" + Math.round(actualMax) + "M",
      "$" + Math.round(actualMin) + "M"
    ],
    textStyle: { color: t.inkSoft, fontSize: 12 },
    calculable: false
  },

  series: [
    {
      name: "Actual",
      type: "heatmap",
      data: actualData,
      label: {
        show: true,
        fontSize: 12,
        color: "#FFFFFF",
        formatter: (p) => "$" + p.value[2].toFixed(1) + "M"
      },
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 1.5
      },
      emphasis: { disabled: true }
    },
    {
      name: "Projected (IBNR)",
      type: "heatmap",
      data: projectedData,
      label: {
        show: true,
        fontSize: 12,
        color: t.inkSoft,
        fontStyle: "italic",
        formatter: (p) => "$" + p.value[2].toFixed(1) + "M"
      },
      itemStyle: {
        color: t.elevatedBg,
        borderColor: t.inkSoft,
        borderWidth: 1
      },
      emphasis: { disabled: true }
    }
  ],

  graphic: [
    {
      type: "group",
      left: 420,
      bottom: 22,
      children: [
        {
          type: "rect",
          shape: { x: 0, y: 2, width: 18, height: 14 },
          style: { fill: t.seq ? t.seq[0] : "#009E73" }
        },
        {
          type: "text",
          x: 22,
          y: 0,
          style: {
            text: "Actual (Observed)",
            fill: t.inkSoft,
            fontSize: 14,
            fontFamily: "sans-serif"
          }
        },
        {
          type: "rect",
          shape: { x: 196, y: 2, width: 18, height: 14 },
          style: {
            fill: t.elevatedBg,
            stroke: t.inkSoft,
            lineWidth: 1
          }
        },
        {
          type: "text",
          x: 218,
          y: 0,
          style: {
            text: "Projected / IBNR",
            fill: t.inkSoft,
            fontSize: 14,
            fontFamily: "sans-serif"
          }
        }
      ]
    }
  ]
});
