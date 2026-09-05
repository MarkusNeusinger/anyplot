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
const peakValue = Math.max(...hourlyInstances);
const peakHour = hourlyInstances.indexOf(peakValue);

const data = [];
let previousValue = null;
for (let hour = 0; hour < hourlyInstances.length; hour += 1) {
  const value = hourlyInstances[hour];
  const isStepChange = value !== previousValue;
  for (let sample = 0; sample < samplesPerHour; sample += 1) {
    const point = { x: hour + sample / samplesPerHour, y: value };
    // Mark the instant the autoscaler actually resizes the group, so the
    // discrete step change (not a smooth ramp) reads at a glance.
    if (isStepChange && sample === 0) {
      point.marker = { enabled: true, radius: 4, fillColor: t.palette[0] };
    }
    if (hour === peakHour && sample === 0) {
      point.dataLabels = {
        enabled: true,
        format: "Peak: {y} instances",
        style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
        y: -16,
      };
    }
    data.push(point);
  }
  previousValue = value;
}

// --- Chart -----------------------------------------------------------------
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
    max: 18,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    // Highcharts' post-alignment step: the new count takes effect exactly at
    // the hour it starts, matching the autoscaler's actual resize instant.
    // A low-opacity fill under the step line adds visual hierarchy beyond a
    // bare line, and per-point markers/dataLabels above call out the
    // discrete change points and the peak instance count.
    area: {
      step: "right",
      lineWidth: 2.5,
      fillOpacity: 0.12,
      marker: { enabled: false },
      dataLabels: { enabled: false },
    },
  },
  series: [{ name: "Active Instances", data, color: t.palette[0] }],
});
