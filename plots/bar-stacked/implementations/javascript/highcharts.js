// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// National electricity generation mix by source, 2019-2024 (TWh)
const years = ["2019", "2020", "2021", "2022", "2023", "2024"];
const sources = [
  { name: "Solar", data: [18, 24, 33, 46, 62, 81] },
  { name: "Wind", data: [61, 68, 74, 79, 86, 93] },
  { name: "Hydro", data: [92, 90, 88, 91, 89, 87] },
  { name: "Natural Gas", data: [145, 138, 130, 118, 104, 92] },
  { name: "Coal", data: [96, 78, 62, 47, 33, 21] },
];

const series = sources.map((s, i) => ({
  name: s.name,
  data: s.data,
  color: t.palette[i],
}));

// --- Chart -------------------------------------------------------------------
const title = "bar-stacked · javascript · highcharts · anyplot.ai";

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
  subtitle: {
    text: "Electricity generation mix by source (TWh)",
    style: { color: t.inkSoft, fontSize: "14px" },
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
    title: {
      text: "Generation (TWh)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    stackLabels: {
      enabled: true,
      style: {
        color: t.inkSoft,
        fontSize: "14px",
        fontWeight: "normal",
        textOutline: "none",
      },
    },
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    column: {
      stacking: "normal",
      borderWidth: 0,
      borderRadius: 2,
    },
  },
  series,
});
