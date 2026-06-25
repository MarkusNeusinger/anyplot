// anyplot.ai
// donut-basic: Basic Donut Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-25
//# anyplot-orientation: square
// anyplot.ai
// donut-basic: Basic Donut Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Data — technology company annual budget allocation
const segments = [
  { name: "R&D", value: 34 },
  { name: "Marketing", value: 22 },
  { name: "Operations", value: 18 },
  { name: "HR & Admin", value: 12 },
  { name: "Infrastructure", value: 9 },
  { name: "Legal & Finance", value: 5 },
];

const cx = size.width * 0.50;
const cy = size.height * 0.46;

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "donut-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22 },
  },

  legend: {
    orient: "horizontal",
    bottom: "4%",
    left: "center",
    itemWidth: 14,
    itemHeight: 14,
    itemGap: 20,
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },

  graphic: [
    {
      type: "text",
      style: {
        text: "Budget",
        x: cx,
        y: cy - 22,
        textAlign: "center",
        fill: t.ink,
        fontSize: 26,
        fontWeight: "bold",
      },
    },
    {
      type: "text",
      style: {
        text: "Allocation",
        x: cx,
        y: cy + 12,
        textAlign: "center",
        fill: t.inkSoft,
        fontSize: 18,
      },
    },
  ],

  series: [
    {
      type: "pie",
      radius: ["38%", "65%"],
      center: ["50%", "46%"],
      avoidLabelOverlap: true,
      data: segments,
      label: {
        show: true,
        position: "outside",
        formatter: "{d}%",
        color: t.ink,
        fontSize: 16,
        fontWeight: "bold",
      },
      labelLine: {
        lineStyle: { color: t.inkSoft, width: 1.5 },
        length: 15,
        length2: 25,
      },
      itemStyle: {
        borderWidth: 3,
        borderColor: t.pageBg,
        borderRadius: 3,
      },
      emphasis: { disabled: true },
    },
  ],
});
