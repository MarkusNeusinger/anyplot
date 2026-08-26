// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Quarterly revenue by product line, in $M.
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const hardware = [41, 38, 44, 51];
const software = [27, 32, 35, 39];
const services = [18, 21, 19, 24];
const support = [11, 14, 13, 16];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "bar-stacked-labeled · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: quarters,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Revenue ($M)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    endOnTick: false,
    maxPadding: 0.14,
    stackLabels: {
      enabled: true,
      style: {
        color: t.ink,
        fontSize: "17px",
        fontWeight: "700",
        textOutline: "none",
      },
      formatter: function () {
        return "$" + this.total + "M";
      },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    column: {
      borderWidth: 0,
      stacking: "normal",
      pointPadding: 0.08,
      groupPadding: 0.14,
    },
  },
  series: [
    { name: "Hardware", data: hardware },
    { name: "Software", data: software },
    { name: "Services", data: services },
    { name: "Support", data: support },
  ],
});
