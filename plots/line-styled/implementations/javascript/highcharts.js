// anyplot.ai
// line-styled: Styled Line Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Server resource utilization sampled every 30 minutes over a 24-hour window.
// Four metrics are distinguished by line style so the chart still reads once
// printed in black and white.
const hours = [];
for (let i = 0; i <= 48; i++) hours.push(i / 2);

const cpuLoad = hours.map((h) => 42 + 22 * Math.sin((h / 24) * 2 * Math.PI - 1.2) + 6 * Math.sin((h / 3) * 2 * Math.PI));
const memoryUse = hours.map((h) => 58 + 9 * Math.sin((h / 24) * 2 * Math.PI - 0.4) + h * 0.15);
const networkIo = hours.map((h) => 30 + 28 * Math.max(0, Math.sin((h / 12) * 2 * Math.PI)) + 4 * Math.sin((h / 1.5) * 2 * Math.PI));
const diskIo = hours.map((h) => 18 + 6 * Math.sin((h / 8) * 2 * Math.PI + 0.8) + 0.3 * h);

const toPoints = (series) => hours.map((h, i) => [h, Math.round(series[i] * 10) / 10]);

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
    text: "line-styled · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Time of Day (hours)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    min: 0,
    max: 24,
    tickInterval: 4,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return `${this.value}:00`;
      },
    },
    // CPU and Memory both crest in this window (see data formulas above) —
    // a plotBand calls out the one moment worth noticing among four equally-weighted lines.
    plotBands: [
      {
        from: 8.5,
        to: 10.5,
        color: t.elevatedBg,
        label: {
          text: "CPU + Memory peak",
          style: { color: t.inkSoft, fontSize: "12px" },
          verticalAlign: "top",
          y: 16,
        },
      },
    ],
  },
  yAxis: {
    title: { text: "Utilization (%)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    min: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: {
      animation: false,
      marker: { enabled: false },
      lineWidth: 3,
    },
  },
  series: [
    { name: "CPU", data: toPoints(cpuLoad), dashStyle: "Solid" },
    { name: "Memory", data: toPoints(memoryUse), dashStyle: "Dash" },
    { name: "Network I/O", data: toPoints(networkIo), dashStyle: "Dot" },
    { name: "Disk I/O", data: toPoints(diskIo), dashStyle: "DashDot" },
  ],
});
