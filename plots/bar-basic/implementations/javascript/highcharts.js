// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
const departments = [
  "Engineering",
  "Sales",
  "Support",
  "Marketing",
  "Operations",
  "Finance",
];
const headcount = [186, 142, 97, 68, 54, 31];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: [t.palette[0]],
  title: {
    text: "bar-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: departments,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: null },
  },
  yAxis: {
    title: {
      text: "Headcount",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 0,
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    column: {
      borderWidth: 0,
      borderRadius: 2,
      pointPadding: 0.12,
      groupPadding: 0.08,
      dataLabels: {
        enabled: true,
        style: {
          color: t.inkSoft,
          fontSize: "14px",
          fontWeight: "500",
          textOutline: "none",
        },
      },
    },
  },
  series: [{ name: "Headcount", data: headcount }],
});
