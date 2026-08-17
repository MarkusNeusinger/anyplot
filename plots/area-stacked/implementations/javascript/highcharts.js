// anyplot.ai
// area-stacked: Stacked Area Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-17

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// US energy consumption by sector, 2015-2024 (quadrillion BTU, illustrative)
const years = Array.from({ length: 10 }, (_, i) => 2015 + i);

const industrial = [31.8, 32.1, 32.6, 33.4, 33.0, 30.9, 32.5, 33.7, 34.1, 34.5];
const transportation = [27.1, 27.5, 27.9, 28.3, 28.2, 24.6, 26.4, 27.1, 27.4, 27.6];
const residential = [21.4, 20.6, 20.9, 21.6, 21.2, 20.8, 21.9, 21.5, 21.3, 21.6];
const commercial = [18.3, 18.1, 18.0, 18.4, 18.1, 16.9, 17.6, 18.0, 18.2, 18.4];
const agriculture = [2.4, 2.5, 2.5, 2.6, 2.6, 2.5, 2.6, 2.7, 2.7, 2.8];

// --- Chart -------------------------------------------------------------------
const title = "area-stacked · javascript · highcharts · anyplot.ai";

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
    text: title,
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: years.map(String),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Year", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: 0,
    title: {
      text: "Energy Consumption (quadrillion BTU)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    stackLabels: {
      enabled: true,
      style: { color: t.inkSoft, fontSize: "12px", fontWeight: "normal", textOutline: "none" },
      formatter: function () {
        return Math.round(this.total);
      },
    },
  },
  legend: {
    reversed: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
    area: {
      stacking: "normal",
      lineWidth: 2,
      fillOpacity: 0.8,
      lineColor: undefined,
    },
  },
  series: [
    // Highcharts stacks the last-defined series at the base of the stack, so
    // the array runs smallest-to-largest (Agriculture first) to put the
    // largest series (Industrial) at the bottom per the spec's guidance.
    { name: "Agriculture", data: agriculture, color: t.palette[4] },
    { name: "Commercial", data: commercial, color: t.palette[3] },
    { name: "Residential", data: residential, color: t.palette[2] },
    { name: "Transportation", data: transportation, color: t.palette[1] },
    { name: "Industrial", data: industrial, color: t.palette[0] },
  ],
});
