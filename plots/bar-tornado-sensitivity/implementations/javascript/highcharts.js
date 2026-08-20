// anyplot.ai
// bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// One-way sensitivity analysis: NPV of a solar farm project ($ millions) under
// low/high scenarios for each input assumption, varied one at a time.
const BASE_VALUE = 12.4;
const parameters = [
  { name: "Electricity Price", low: 8.9, high: 15.7 },
  { name: "Discount Rate", low: 15.8, high: 9.1 },
  { name: "Capital Cost", low: 14.6, high: 10.1 },
  { name: "O&M Cost", low: 13.5, high: 11.2 },
  { name: "Panel Degradation Rate", low: 13.1, high: 11.5 },
  { name: "Debt Interest Rate", low: 13.0, high: 11.7 },
  { name: "Construction Delay", low: 12.9, high: 11.6 },
  { name: "Tax Credit Rate", low: 12.0, high: 12.9 },
];

// Sorted descending by impact range so the widest bar lands at the top —
// Highcharts' "bar" (horizontal) type renders category index 0 at the top.
const categories = parameters.map((p) => p.name);
const highDeltas = parameters.map((p) => +(p.high - BASE_VALUE).toFixed(1));
const lowDeltas = parameters.map((p) => +(p.low - BASE_VALUE).toFixed(1));

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
    text: "bar-tornado-sensitivity · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Project NPV ($ millions)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter: function () {
        return "$" + (BASE_VALUE + this.value).toFixed(1) + "M";
      },
    },
    plotLines: [
      {
        value: 0,
        color: t.ink,
        width: 2,
        zIndex: 5,
        label: {
          text: "Base case: $" + BASE_VALUE.toFixed(1) + "M",
          rotation: 0,
          align: "left",
          verticalAlign: "top",
          x: 8,
          y: 16,
          style: { color: t.inkSoft, fontSize: "13px" },
        },
      },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter: function () {
      return (
        this.series.name +
        ": <b>$" +
        (BASE_VALUE + this.y).toFixed(1) +
        "M</b>"
      );
    },
  },
  plotOptions: {
    series: { animation: false, stacking: "normal", pointPadding: 0.08, groupPadding: 0.12 },
    bar: { borderWidth: 0 },
  },
  series: [
    {
      name: "High input scenario",
      data: highDeltas,
      color: t.palette[0],
      dataLabels: {
        enabled: true,
        color: t.ink,
        style: { fontSize: "13px", fontWeight: "500", textOutline: "none" },
        formatter: function () {
          return "$" + (BASE_VALUE + this.y).toFixed(1) + "M";
        },
      },
    },
    {
      name: "Low input scenario",
      data: lowDeltas,
      color: t.palette[1],
      dataLabels: {
        enabled: true,
        color: t.ink,
        style: { fontSize: "13px", fontWeight: "500", textOutline: "none" },
        formatter: function () {
          return "$" + (BASE_VALUE + this.y).toFixed(1) + "M";
        },
      },
    },
  ],
});
