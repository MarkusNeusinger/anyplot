// anyplot.ai
// line-filled: Filled Line Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly website traffic (thousands of sessions) over two years.
const months = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

let sessions = 40;
const traffic = months.map((_, i) => {
  const seasonal = 12 * Math.sin((i / 12) * Math.PI * 2 - Math.PI / 2);
  const trend = i * 0.9;
  const noise = (rand() - 0.5) * 6;
  sessions = 40 + trend + seasonal + noise;
  return Math.round(Math.max(sessions, 5) * 10) / 10;
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Website Traffic · line-filled · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 110, bottom: 80 },
  xAxis: {
    type: "category",
    data: months,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Sessions (thousands)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: traffic,
      showSymbol: false,
      smooth: 0.2,
      lineStyle: { width: 3.5, color: t.palette[0] },
      areaStyle: { color: t.palette[0], opacity: 0.35 },
    },
  ],
});
