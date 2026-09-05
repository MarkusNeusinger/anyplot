// anyplot.ai
// line-stepwise: Step Line Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Smart thermostat target-temperature schedule: the setpoint changes at a
// handful of events per day and holds constant until the next event — a
// textbook piecewise-constant signal, sampled across 8 days.
const DAILY_SCHEDULE = [
  [0, 18],
  [5.5, 19],
  [6.5, 21],
  [8, 18],
  [17, 20],
  [18.5, 22],
  [22, 18],
];

const hours = [];
const setpoints = [];
for (let day = 0; day < 8; day++) {
  for (const [hourOfDay, tempC] of DAILY_SCHEDULE) {
    hours.push(day * 24 + hourOfDay);
    setpoints.push(tempC);
  }
}
const data = hours.map((h, i) => [h, setpoints[i]]);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "line-stepwise · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  tooltip: { trigger: "axis" },
  grid: { left: 90, right: 60, top: 100, bottom: 80 },
  xAxis: {
    type: "value",
    name: "Time (days)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 192,
    interval: 24,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => `Day ${v / 24 + 1}` },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Target Temperature (°C)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 16,
    max: 24,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}°C" },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: data,
      step: "end",
      symbol: "circle",
      symbolSize: 8,
      lineStyle: { color: t.palette[0], width: 3.5 },
      itemStyle: { color: t.palette[0] },
      areaStyle: { color: t.palette[0], opacity: 0.12 },
    },
  ],
});
