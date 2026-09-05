// anyplot.ai
// scatter-annotated: Annotated Scatter Plot with Text Labels
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 77/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Revenue vs. market cap for a set of well-known tech companies (illustrative
// figures, not live market data). Labels annotate every point since n is small.
const companies = [
  { name: "Apple", revenue: 383, marketCap: 2950 },
  { name: "Microsoft", revenue: 212, marketCap: 3100 },
  { name: "Alphabet", revenue: 307, marketCap: 1850 },
  { name: "Amazon", revenue: 575, marketCap: 1900 },
  { name: "Nvidia", revenue: 61, marketCap: 2200 },
  { name: "Meta", revenue: 135, marketCap: 1250 },
  { name: "Tesla", revenue: 97, marketCap: 780 },
  { name: "Broadcom", revenue: 35, marketCap: 610 },
  { name: "Oracle", revenue: 50, marketCap: 330 },
  { name: "Adobe", revenue: 19, marketCap: 230 },
  { name: "Salesforce", revenue: 34, marketCap: 260 },
  { name: "IBM", revenue: 61, marketCap: 175 },
  { name: "Intel", revenue: 54, marketCap: 105 },
  { name: "Cisco", revenue: 57, marketCap: 200 },
  { name: "Uber", revenue: 37, marketCap: 145 },
];

const points = companies.map((c) => ({
  x: c.revenue,
  y: c.marketCap,
  name: c.name,
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "scatter-annotated · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "logarithmic",
    title: {
      text: "Annual Revenue (USD billions, log scale)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    type: "logarithmic",
    title: {
      text: "Market Cap (USD billions, log scale)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: {
    pointFormat: "Revenue: {point.x}B · Market Cap: {point.y}B",
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: {
        radius: 7,
        fillColor: Highcharts.color(t.palette[0]).setOpacity(0.7).get(),
        lineWidth: 1,
        lineColor: t.pageBg,
      },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        align: "left",
        x: 10,
        y: 4,
        allowOverlap: false,
        style: {
          color: t.ink,
          fontSize: "13px",
          fontWeight: "normal",
          textOutline: "none",
        },
      },
    },
  },
  series: [
    {
      name: "Companies",
      data: points,
      color: t.palette[0],
    },
  ],
});
