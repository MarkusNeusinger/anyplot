// anyplot.ai
// bar-stacked-percent: 100% Stacked Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-18

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Cloud infrastructure market share by provider, 2019-2024 (illustrative
// quarterly revenue share, USD billions) — normalized to 100% per year.
const years = ["2019", "2020", "2021", "2022", "2023", "2024"];
const aws = [47, 45, 40, 34, 32, 31];
const azure = [22, 24, 27, 26, 25, 24];
const gcp = [8, 9, 10, 11, 11, 12];
const other = [23, 22, 23, 29, 32, 33];

// Segments below this share (%) skip their data label to avoid crowding —
// Google Cloud's ~8-12% band is the thinnest and stays label-free.
const MIN_LABEL_SHARE = 13;

// --- Chart -------------------------------------------------------------------
const title = "bar-stacked-percent · javascript · highcharts · anyplot.ai";

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
    text: title,
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: years,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Year", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: 0,
    max: 100,
    tickInterval: 20,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    title: {
      text: "Market Share (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      format: "{value}%",
      style: { color: t.inkSoft, fontSize: "14px" },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    enabled: true,
    shared: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.inkSoft,
    style: { color: t.ink, fontSize: "13px" },
    headerFormat: '<span style="font-weight:600">{point.key}</span><br/>',
    pointFormat:
      '<span style="color:{point.color}">●</span> {series.name}: <b>{point.percentage:.0f}%</b> ({point.y})<br/>',
  },
  plotOptions: {
    series: { animation: false },
    column: {
      stacking: "percent",
      borderWidth: 2,
      borderColor: t.pageBg,
      borderRadius: 3,
      pointPadding: 0.08,
      groupPadding: 0.12,
      dataLabels: {
        enabled: true,
        formatter: function () {
          return this.percentage >= MIN_LABEL_SHARE ? Math.round(this.percentage) + "%" : null;
        },
        style: {
          color: "#FFFFFF",
          fontSize: "13px",
          fontWeight: "600",
          textOutline: "1px rgba(26, 26, 23, 0.55)",
        },
      },
    },
  },
  series: [
    { name: "AWS", data: aws, color: t.palette[0] },
    { name: "Microsoft Azure", data: azure, color: t.palette[1] },
    { name: "Google Cloud", data: gcp, color: t.palette[2] },
    { name: "Other Providers", data: other, color: t.palette[3] },
  ],
});
