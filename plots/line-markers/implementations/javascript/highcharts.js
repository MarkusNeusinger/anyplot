// anyplot.ai
// line-markers: Line Plot with Markers
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Weekly hardness readings (Rockwell HRC) from two heat-treatment furnace runs.
// Furnace B week 7 dips below the minimum spec after a refractory lining check.
const weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const MIN_SPEC_HRC = 56;
const furnaceA = [58.2, 59.1, 57.8, 60.3, 59.6, 61.2, 60.8, 62.1, 61.5, 63.0];
const furnaceB = [
  55.4,
  56.0,
  57.3,
  56.8,
  58.1,
  57.6,
  {
    y: 52.5,
    marker: { radius: 9, fillColor: t.amber, lineColor: t.ink, lineWidth: 2 },
    dataLabels: {
      enabled: true,
      format: "Refractory dip",
      align: "right",
      x: -12,
      y: 18,
      style: { color: t.ink, fontSize: "12px", fontWeight: "600", textOutline: "none" },
    },
  },
  58.4,
  59.8,
  60.2,
];

const title = "line-markers · javascript · highcharts · anyplot.ai";

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
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
    categories: weeks.map((w) => `Week ${w}`),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: {
      text: "Production Week",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
  },
  yAxis: {
    title: {
      text: "Hardness (HRC)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: MIN_SPEC_HRC,
        color: t.amber,
        width: 1.5,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `Min spec: ${MIN_SPEC_HRC} HRC`,
          align: "left",
          x: 4,
          y: -6,
          style: { color: t.inkSoft, fontSize: "12px", fontWeight: "600" },
        },
      },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: {
      animation: false,
      lineWidth: 2.5,
      marker: { radius: 6, lineWidth: 1.5, lineColor: t.pageBg },
    },
  },
  series: [
    {
      name: "Furnace A",
      data: [
        ...furnaceA.slice(0, -1),
        {
          y: furnaceA[furnaceA.length - 1],
          dataLabels: {
            enabled: true,
            format: "+2.8 HRC vs B",
            align: "center",
            y: -18,
            style: { color: t.ink, fontSize: "12px", fontWeight: "600", textOutline: "none" },
          },
        },
      ],
      marker: { symbol: "circle" },
    },
    {
      name: "Furnace B",
      data: furnaceB,
      marker: { symbol: "diamond" },
      dashStyle: "ShortDash",
    },
  ],
});
