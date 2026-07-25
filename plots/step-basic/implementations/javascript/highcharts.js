// anyplot.ai
// step-basic: Basic Step Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Hourly active-instance count for an auto-scaling web service: capacity only
// changes at discrete scaling events, holding steady in between — a natural
// fit for a step plot's "post" style (value holds from this hour until the
// next scaling decision).
const hours = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
  22, 23,
];
const instances = [
  2, 2, 2, 2, 2, 3, 3, 4, 6, 8, 8, 10, 10, 10, 9, 9, 8, 8, 7, 6, 4, 3, 2, 2,
];
const data = hours.map((h, i) => [h, instances[i]]);

// Peak scaling window (hours 11-13, where capacity plateaus at 10 instances) —
// called out with a plotBand so the step's flat top reads as a deliberate
// signal rather than just "the highest bar".
const peakBandColor = Highcharts.color(t.palette[0]).setOpacity(0.12).get();

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
    text: "step-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Hour of Day", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    tickInterval: 2,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotBands: [
      {
        from: 10.5,
        to: 13.5,
        color: peakBandColor,
        label: {
          text: "Peak scaling window",
          style: { color: t.inkSoft, fontSize: "12px" },
          y: 16,
        },
      },
    ],
  },
  yAxis: {
    title: {
      text: "Active Instances",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 0,
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    area: {
      step: "right",
      lineWidth: 2.5,
      fillOpacity: 0.15,
      marker: { enabled: true, radius: 5 },
    },
  },
  series: [
    {
      name: "Active instances",
      data,
    },
  ],
});
