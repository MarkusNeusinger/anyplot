// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 79/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue ($M) by product line across sales regions.
const regions = ["North America", "Europe", "Asia Pacific", "Latin America"];
const productLines = ["Software", "Hardware", "Services"];
const revenueByProduct = [
  [42.5, 31.2, 27.8, 12.4], // Software
  [28.1, 24.6, 33.5, 9.8], // Hardware
  [19.7, 22.3, 15.9, 7.1], // Services
];

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
    text: "bar-grouped · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: regions,
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
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false, groupPadding: 0.1, pointPadding: 0.05 },
    column: { borderWidth: 0 },
  },
  series: productLines.map((name, i) => ({
    name,
    data: revenueByProduct[i],
  })),
});
