// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) — most populous countries, ascending ---
// renders smallest (Mexico) at top to largest (India) at bottom, matching array order.
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

// Highlight the top-ranked country (India) at full brand-green; mute the rest
// to a lower-opacity tint of the same hue so the largest value reads as the
// chart's focal point (spec: "highlight specific bars to draw attention").
const topIndex = population.length - 1;
const mutedGreen = Highcharts.color(t.palette[0]).setOpacity(0.5).get();
const seriesData = population.map((value, i) => ({
  y: value,
  color: i === topIndex ? t.palette[0] : mutedGreen,
  dataLabels: i === topIndex ? { style: { fontWeight: "700" } } : undefined,
}));

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
      data: seriesData,
    },
  ],
});
