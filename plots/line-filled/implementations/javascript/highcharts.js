// anyplot.ai
// line-filled: Filled Line Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic — daily reservoir level over 30 days) --
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const days = Array.from({ length: 30 }, (_, i) => i);
const levels = [];
let level = 42;
for (let i = 0; i < days.length; i++) {
  level += (rand() - 0.42) * 4;
  level = Math.max(20, level);
  levels.push(Math.round(level * 10) / 10);
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "Reservoir Water Level · line-filled · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Day", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    categories: days.map(String),
    tickInterval: 5,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Water Level (m)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
    headerFormat: "Day {point.key}<br/>",
    pointFormat: "Water Level: <b>{point.y} m</b>",
  },
  plotOptions: {
    series: { animation: false },
    area: {
      lineWidth: 2.5,
      color: t.palette[0],
      fillColor: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, t.palette[0] + "8C"],
          [1, t.palette[0] + "21"],
        ],
      },
      marker: { enabled: true, radius: 3, fillColor: t.palette[0], lineWidth: 0 },
      threshold: 0,
    },
  },
  series: [{ name: "Water Level", data: levels }],
});
