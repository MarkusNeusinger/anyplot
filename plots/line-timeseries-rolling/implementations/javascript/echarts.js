// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
// Hourly outdoor temperature readings over 10 days with a 24-hour rolling mean.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const HOURS = 240;
const WINDOW = 24;
const startDate = new Date("2024-06-01T00:00:00Z");

const times = [];
const temperatures = [];
for (let i = 0; i < HOURS; i++) {
  times.push(new Date(startDate.getTime() + i * 3600 * 1000));
  const dailyCycle = 6 * Math.sin(((i % 24) / 24) * 2 * Math.PI - Math.PI / 2);
  const seasonalDrift = 3 * Math.sin((i / HOURS) * Math.PI);
  const noise = (lcgRandom() - 0.5) * 4;
  temperatures.push(18 + dailyCycle + seasonalDrift + noise);
}

const rawSeries = times.map((ts, i) => [ts, temperatures[i]]);
const rollingSeries = times.map((ts, i) => {
  if (i < WINDOW - 1) return [ts, null];
  let sum = 0;
  for (let j = i - WINDOW + 1; j <= i; j++) sum += temperatures[j];
  return [ts, sum / WINDOW];
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[0], t.palette[1]],
  backgroundColor: "transparent",
  title: {
    text: "line-timeseries-rolling · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 100, bottom: 160 },
  legend: {
    data: ["Raw Data", "24-Hour Rolling Average"],
    bottom: 15,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    itemWidth: 24,
    itemHeight: 3,
  },
  tooltip: { trigger: "axis" },
  dataZoom: [
    { type: "inside", xAxisIndex: 0 },
    {
      type: "slider",
      xAxisIndex: 0,
      bottom: 60,
      height: 20,
      borderColor: t.grid,
      fillerColor: `${t.palette[0]}33`,
      handleStyle: { color: t.palette[0] },
      textStyle: { color: t.inkSoft, fontSize: 12 },
      dataBackground: {
        lineStyle: { color: t.inkSoft },
        areaStyle: { color: t.grid },
      },
    },
  ],
  xAxis: {
    type: "time",
    name: "Date / Hour (UTC)",
    nameLocation: "middle",
    nameGap: 32,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    scale: true,
    name: "Temperature (°C)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Raw Data",
      type: "line",
      data: rawSeries,
      showSymbol: false,
      lineStyle: { width: 1.5, color: t.palette[0], opacity: 0.35 },
      z: 1,
    },
    {
      name: "24-Hour Rolling Average",
      type: "line",
      data: rollingSeries,
      showSymbol: false,
      lineStyle: { width: 3.5, color: t.palette[1] },
      z: 2,
    },
  ],
});
