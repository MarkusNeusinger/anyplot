// anyplot.ai
// line-stepwise: Step Line Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Active instance count of an autoscaling web-server cluster, sampled every
// 20 minutes. The group only resizes on the hour, so within an hour the
// three samples repeat the same count until the next scaling decision.
const hourlyInstances = [
  3, 3, 2, 2, 2, 2, 3, 4, 6, 8, 10, 12,
  13, 14, 14, 13, 12, 10, 8, 6, 5, 4, 4, 3,
];
const samplesPerHour = 3;
const data = [];
for (let hour = 0; hour < hourlyInstances.length; hour += 1) {
  for (let sample = 0; sample < samplesPerHour; sample += 1) {
    data.push([hour + sample / samplesPerHour, hourlyInstances[hour]]);
  }
}

// --- Chart -----------------------------------------------------------------
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
    text: "line-stepwise · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Hour of Day", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    min: 0,
    max: 24,
    tickInterval: 4,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Active Server Instances", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    min: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    // Highcharts' post-alignment step: the new count takes effect exactly at
    // the hour it starts, matching the autoscaler's actual resize instant.
    line: { step: "right", lineWidth: 2.5, marker: { enabled: false } },
  },
  series: [{ name: "Active Instances", data, color: t.palette[0] }],
});
