// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic, tiny fixed-seed LCG) -------------------
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const dayCount = 60;
const maintenanceWindows = [
  { from: 14, to: 18 },
  { from: 39, to: 43 },
];
const inWindow = (day) => maintenanceWindows.some((w) => day >= w.from && day <= w.to);

const latencyMs = [];
for (let day = 0; day < dayCount; day += 1) {
  const baseline = 120 + 15 * Math.sin(day / 9);
  const spike = inWindow(day) ? 180 + 60 * nextRandom() : 0;
  const noise = (nextRandom() - 0.5) * 16;
  latencyMs.push(Math.round(baseline + spike + noise));
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "span-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "API response latency with scheduled maintenance windows highlighted",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Day of Quarter", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 0,
    max: dayCount - 1,
    tickInterval: 10,
    plotBands: maintenanceWindows.map((w, i) => ({
      from: w.from,
      to: w.to,
      color: `${t.amber}40`,
      label: {
        text: `Maintenance ${i + 1}`,
        style: { color: t.inkSoft, fontSize: "13px" },
        rotation: 0,
        y: 20,
      },
    })),
  },
  yAxis: {
    title: { text: "Response Latency (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    line: { marker: { enabled: false }, lineWidth: 2.5 },
  },
  tooltip: { enabled: false },
  series: [
    {
      name: "Latency",
      data: latencyMs,
      color: t.palette[0],
    },
  ],
});
