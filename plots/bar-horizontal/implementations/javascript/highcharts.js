// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) — most populous countries, ascending ---
// so the largest value renders at the top of the inverted category axis.
const countries = [
  "Mexico",
  "Russia",
  "Bangladesh",
  "Brazil",
  "Nigeria",
  "Pakistan",
  "Indonesia",
  "United States",
  "China",
  "India",
];
const population = [130, 144, 173, 216, 227, 241, 280, 342, 1425, 1441];

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "bar",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "bar-horizontal · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: countries,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: "transparent",
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Population (millions)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    max: 1500,
    tickInterval: 300,
    endOnTick: false,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    bar: {
      borderWidth: 0,
      pointPadding: 0.15,
      groupPadding: 0.1,
      dataLabels: {
        enabled: true,
        format: "{y:,.0f}",
        style: {
          color: t.ink,
          fontSize: "14px",
          fontWeight: "500",
          textOutline: "none",
        },
      },
    },
  },
  tooltip: { enabled: false },
  series: [
    {
      name: "Population",
      data: population,
      color: t.palette[0],
    },
  ],
});
