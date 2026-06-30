// anyplot.ai
// gauge-basic: Basic Gauge Chart
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 88/100 | Created: 2026-06-30

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Net Promoter Score — Q2 2026 customer satisfaction survey (scale 0–100)
const score = 72;

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "gauge-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 28,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
  },
  series: [
    {
      type: "gauge",
      center: ["50%", "54%"],
      radius: "76%",
      min: 0,
      max: 100,
      startAngle: 210,
      endAngle: -30,
      splitNumber: 10,
      axisLine: {
        lineStyle: {
          width: 30,
          color: [
            [0.3, "#AE3030"],  // 0–30: poor (matte red)
            [0.7, "#DDCC77"],  // 30–70: fair (amber)
            [1.0, "#009E73"],  // 70–100: good (brand green)
          ],
        },
      },
      progress: { show: false },
      pointer: {
        length: "65%",
        width: 8,
        itemStyle: { color: t.ink },
      },
      axisTick: {
        splitNumber: 4,
        length: 10,
        lineStyle: { color: "auto", width: 2 },
      },
      splitLine: {
        length: 20,
        lineStyle: { color: "auto", width: 5 },
      },
      axisLabel: {
        color: t.inkSoft,
        fontSize: 14,
        distance: 14,
        formatter: function (value) {
          const zones = [0, 30, 70, 100];
          return zones.includes(Number(value)) ? value : "";
        },
      },
      anchor: {
        show: true,
        showAbove: true,
        size: 22,
        itemStyle: {
          borderWidth: 6,
          borderColor: t.ink,
          color: t.pageBg,
        },
      },
      title: {
        offsetCenter: [0, "22%"],
        fontSize: 18,
        color: t.inkSoft,
        fontWeight: "normal",
      },
      detail: {
        valueAnimation: false,
        fontSize: 60,
        offsetCenter: [0, "58%"],
        formatter: "{value}",
        color: t.ink,
        fontWeight: "bold",
      },
      data: [{ value: score, name: "Net Promoter Score" }],
    },
  ],
});
