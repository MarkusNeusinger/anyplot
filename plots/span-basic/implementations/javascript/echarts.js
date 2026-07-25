// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Hourly server response latency (ms) over one day, with a traffic-spike incident.
const hours = Array.from({ length: 24 }, (_, i) => i);
const latencyMs = [
  95, 88, 102, 91, 85, 79, 83, 110, 135, 128, 118, 125, 132, 140, 310, 340, 295,
  150, 128, 115, 105, 98, 92, 87,
];
const readings = hours.map((h, i) => [h, latencyMs[i]]);

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "span-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 110, right: 60, top: 110, bottom: 80 },
  xAxis: {
    type: "value",
    name: "Time of Day",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 23,
    interval: 3,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: (v) => `${String(Math.round(v)).padStart(2, "0")}:00`,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Response Latency (ms)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: 400,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: readings,
      symbol: "circle",
      symbolSize: 9,
      lineWidth: 3,
      itemStyle: { color: t.palette[0] },
      lineStyle: { color: t.palette[0] },
      markArea: {
        silent: true,
        label: { show: true, formatter: "{b}", color: t.inkSoft, fontSize: 15 },
        data: [
          [
            {
              name: "SLA target (≤200ms)",
              yAxis: 0,
              label: { position: "insideTopLeft" },
              itemStyle: { color: t.palette[0], opacity: 0.16 },
            },
            { yAxis: 200 },
          ],
          [
            {
              name: "Traffic spike incident",
              xAxis: 13.5,
              label: { position: "insideTop" },
              itemStyle: { color: t.amber, opacity: 0.28 },
            },
            { xAxis: 16.5 },
          ],
        ],
      },
    },
  ],
});
