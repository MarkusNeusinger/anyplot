// anyplot.ai
// funnel-basic: Basic Funnel Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const stages = ["Applications", "Screened", "Interviewed", "Offer Extended", "Hired"];
const counts = [2400, 1450, 620, 240, 150];

const funnelData = stages.map((stage, i) => ({ name: stage, value: counts[i] }));

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "funnel-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  tooltip: { show: false },
  legend: {
    show: false,
  },
  series: [
    {
      type: "funnel",
      left: "12%",
      right: "12%",
      top: 110,
      bottom: 60,
      width: "76%",
      min: 0,
      max: counts[0],
      minSize: "10%",
      maxSize: "100%",
      sort: "descending",
      gap: 4,
      label: {
        show: true,
        position: "inside",
        formatter: (params) => `${params.name}\n${params.value.toLocaleString()}`,
        color: t.pageBg,
        fontSize: 16,
        fontWeight: 500,
        lineHeight: 22,
      },
      labelLine: { show: false },
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 2,
      },
      emphasis: { disabled: true },
      data: funnelData,
    },
  ],
});
