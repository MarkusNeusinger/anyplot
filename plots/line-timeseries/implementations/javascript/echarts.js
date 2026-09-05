// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily outdoor temperature readings over 10 months — seasonal trend + noise,
// generated with a fixed-seed LCG since the browser has no seeded RNG.
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const numDays = 300;
const startDate = new Date("2025-01-01T00:00:00Z");
const data = [];
for (let i = 0; i < numDays; i++) {
  const date = new Date(startDate.getTime() + i * 86400000);
  const seasonal = 12 + 10 * Math.sin((2 * Math.PI * i) / 365 - Math.PI / 2);
  const noise = (nextRandom() - 0.5) * 4;
  data.push([date.toISOString().slice(0, 10), Number((seasonal + noise).toFixed(1))]);
}

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Outdoor Temperature · line-timeseries · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 20 },
  },
  grid: { left: 100, right: 70, top: 110, bottom: 90 },
  xAxis: {
    type: "time",
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Temperature (°C)",
    nameTextStyle: { color: t.ink, fontSize: 16 },
    nameGap: 55,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data,
      showSymbol: false,
      smooth: false,
      lineStyle: { color: t.palette[0], width: 3 },
      itemStyle: { color: t.palette[0] },
    },
  ],
});
