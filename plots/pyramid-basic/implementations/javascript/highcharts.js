// anyplot.ai
// pyramid-basic: Basic Pyramid Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Population by age group, in thousands. Male shown as negative (left side).
const ageGroups = [
  "0-9",
  "10-19",
  "20-29",
  "30-39",
  "40-49",
  "50-59",
  "60-69",
  "70-79",
  "80+",
];
const malePopulation = [2450, 2510, 2680, 2920, 3050, 3280, 2870, 1950, 980];
const femalePopulation = [2340, 2400, 2550, 2810, 2990, 3210, 2950, 2180, 1420];
const peakAgeGroup = "50-59"; // widest bulge on both sides, called out below

// --- Chart -------------------------------------------------------------------
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
    text: "pyramid-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: [
    {
      categories: ageGroups,
      reversed: false,
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      labels: { style: { color: t.inkSoft, fontSize: "14px" } },
      title: {
        text: "Age Group",
        style: { color: t.inkSoft, fontSize: "16px" },
      },
    },
    {
      categories: ageGroups,
      opposite: true,
      reversed: false,
      linkedTo: 0,
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      labels: { style: { color: t.inkSoft, fontSize: "14px" } },
      title: { text: null },
    },
  ],
  yAxis: {
    min: -3500,
    max: 3500,
    tickInterval: 1000,
    gridLineColor: t.grid,
    title: {
      text: "Population",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return Math.abs(this.value) + "k";
      },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter() {
      return `${this.series.name}, ${this.point.category}: ${Math.abs(this.point.y)}k`;
    },
  },
  plotOptions: {
    series: {
      animation: false,
      stacking: "normal",
      borderWidth: 0,
      pointPadding: 0.1,
      groupPadding: 0,
      dataLabels: {
        enabled: true,
        style: {
          color: t.ink,
          fontSize: "13px",
          fontWeight: "700",
          textOutline: "none",
        },
        formatter() {
          if (this.point.category !== peakAgeGroup) return null;
          return `${Math.abs(this.y)}k peak`;
        },
      },
    },
  },
  series: [
    { name: "Male", data: malePopulation.map((v) => -v) },
    { name: "Female", data: femalePopulation },
  ],
});
