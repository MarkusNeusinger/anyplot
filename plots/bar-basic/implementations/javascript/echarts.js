// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 93/100 | Created: 2026-06-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Data — monthly book loans at a city library (thousands)
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const loans  = [18.4, 21.7, 26.2, 31.5, 35.8, 41.3,
                47.1, 44.6, 35.9, 29.8, 24.2, 27.6];

// Highlight the seasonal peak; fade the rest for hierarchy
const peakIdx = loans.indexOf(Math.max(...loans));
const bars = loans.map((v, i) => ({
  value: v,
  itemStyle: {
    color: t.palette[0],
    opacity: i === peakIdx ? 1 : 0.55,
    borderRadius: [4, 4, 0, 0],
  },
}));

// Init
const chart = echarts.init(document.getElementById("container"));

// Option
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Books Borrowed per Month · bar-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 28,
    textStyle: { color: t.ink, fontSize: 30, fontWeight: 500 },
  },
  grid: { left: 110, right: 60, top: 130, bottom: 100, containLabel: false },
  xAxis: {
    type: "category",
    data: months,
    name: "Month",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.ink, fontSize: 24 },
    axisLabel: { color: t.inkSoft, fontSize: 20, margin: 16 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Loans (thousands)",
    nameLocation: "middle",
    nameGap: 78,
    nameTextStyle: { color: t.ink, fontSize: 24 },
    axisLabel: { color: t.inkSoft, fontSize: 20, margin: 12 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid, width: 1 } },
  },
  series: [{
    type: "bar",
    data: bars,
    barWidth: "62%",
    label: {
      show: true,
      position: "top",
      color: t.inkSoft,
      fontSize: 16,
      formatter: (p) => p.value.toFixed(1),
    },
    markLine: {
      silent: true,
      symbol: "none",
      data: [{ type: "average", name: "Avg" }],
      lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5, opacity: 0.8 },
      label: {
        color: t.inkSoft,
        fontSize: 16,
        position: "insideEndTop",
        formatter: (p) => `Avg ${p.value.toFixed(1)}`,
      },
    },
  }],
});

window.addEventListener("resize", () => chart.resize());
chart.on("finished", () => { window.__anyplotReady = true; });
