// anyplot.ai
// bar-diverging: Diverging Bar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Net satisfaction score (-100..+100) per product category, ascending so the
// horizontal bars read bottom (most negative) to top (most positive).
const categories = [
  "DVD Rental Service",
  "Legacy Software Suite",
  "Landline Phone Service",
  "Print Newsletter Subscription",
  "Cable TV Package",
  "Physical Retail Store",
  "Mobile Banking App",
  "Streaming Video Service",
  "Cloud Storage Plan",
  "Wireless Earbuds",
];
const netSatisfaction = [-61, -52, -41, -38, -29, -12, 34, 47, 58, 66];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "bar",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "bar-diverging · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Net satisfaction score by product category, sorted low to high",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Net Satisfaction Score", style: { color: t.inkSoft, fontSize: "16px" } },
    min: -80,
    max: 80,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [{ value: 0, color: t.inkSoft, width: 2, zIndex: 5 }],
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    bar: {
      borderWidth: 0,
      pointPadding: 0.1,
      groupPadding: 0.05,
      dataLabels: {
        enabled: true,
        color: t.ink,
        style: { fontSize: "13px", fontWeight: "500", textOutline: "none" },
        formatter() {
          return (this.y > 0 ? "+" : "") + this.y;
        },
      },
    },
  },
  series: [
    {
      name: "Net Satisfaction",
      data: netSatisfaction,
      color: t.palette[0],
      negativeColor: t.palette[4],
    },
  ],
});
