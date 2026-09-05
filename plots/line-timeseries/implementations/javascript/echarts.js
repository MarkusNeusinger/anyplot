// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily outdoor temperature readings over a full year — seasonal trend + noise,
// generated with a fixed-seed LCG since the browser has no seeded RNG.
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const numDays = 365;
const startDate = new Date("2025-01-01T00:00:00Z");
const data = [];
let peak = { date: null, value: -Infinity };
let trough = { date: null, value: Infinity };
for (let i = 0; i < numDays; i++) {
  const date = new Date(startDate.getTime() + i * 86400000);
  const isoDate = date.toISOString().slice(0, 10);
  const seasonal = 12 + 10 * Math.sin((2 * Math.PI * i) / 365 - Math.PI / 2);
  const noise = (nextRandom() - 0.5) * 4;
  const value = Number((seasonal + noise).toFixed(1));
  data.push([isoDate, value]);
  if (value > peak.value) peak = { date: isoDate, value };
  if (value < trough.value) trough = { date: isoDate, value };
}
const average = Number(
  (data.reduce((sum, [, v]) => sum + v, 0) / data.length).toFixed(1)
);

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
  dataZoom: [{ type: "inside" }],
  xAxis: {
    type: "time",
    name: "Date",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grid, opacity: 0.6 } },
  },
  yAxis: {
    type: "value",
    name: "Temperature (°C)",
    nameTextStyle: { color: t.ink, fontSize: 16 },
    nameGap: 55,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid, opacity: 0.6 } },
  },
  series: [
    {
      type: "line",
      data,
      showSymbol: false,
      smooth: false,
      lineStyle: { color: t.palette[0], width: 3 },
      itemStyle: { color: t.palette[0] },
      markPoint: {
        symbol: "circle",
        symbolSize: 10,
        itemStyle: { color: t.palette[0] },
        label: { color: t.ink, fontSize: 13, formatter: (p) => `${p.value}°C` },
        data: [
          { name: "Peak", coord: [peak.date, peak.value], value: peak.value },
          {
            name: "Trough",
            coord: [trough.date, trough.value],
            value: trough.value,
            label: { position: "right", offset: [8, 0] },
          },
        ],
      },
      markLine: {
        symbol: "none",
        label: { color: t.inkSoft, fontSize: 13, formatter: `Avg ${average}°C` },
        lineStyle: { color: t.inkSoft, type: "dashed" },
        data: [{ yAxis: average }],
      },
    },
  ],
});
