// anyplot.ai
// bar-error: Bar Chart with Error Bars
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
const categories = ["Control", "Drug A", "Drug B", "Drug C", "Drug D", "Drug E"];
const meanActivity = [42.3, 58.1, 71.4, 49.8, 63.2, 55.6];
const stdDev = [4.1, 6.8, 5.2, 7.3, 4.9, 6.1];

// Only the core Highcharts bundle is loaded (no highcharts-more), so the
// errorbar series type isn't available. Error bars are composed instead from
// a plain "line" series: a vertical whisker plus top/bottom caps per category,
// each segment separated by a null-y gap point so they don't connect to each
// other. The gap points still carry an explicit `x` — a bare `null` array
// entry has no x, and Highcharts then auto-indexes it sequentially, which
// silently stretches the category axis with phantom trailing categories.
const CAP_HALF_WIDTH = 0.18;
const errorBarData = [];
categories.forEach((_, i) => {
  const low = meanActivity[i] - stdDev[i];
  const high = meanActivity[i] + stdDev[i];
  errorBarData.push(
    { x: i - CAP_HALF_WIDTH, y: high },
    { x: i + CAP_HALF_WIDTH, y: high },
    { x: i, y: null },
    { x: i, y: high },
    { x: i, y: low },
    { x: i, y: null },
    { x: i - CAP_HALF_WIDTH, y: low },
    { x: i + CAP_HALF_WIDTH, y: low },
    { x: i, y: null },
  );
});

// --- Chart -------------------------------------------------------------------
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
    text: "bar-error · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Error bars show ±1 standard deviation",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Enzyme Activity (U/mg)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    column: { borderWidth: 0, pointPadding: 0.15, groupPadding: 0.1 },
  },
  series: [
    {
      name: "Enzyme activity",
      type: "column",
      data: meanActivity,
      color: t.palette[0],
      showInLegend: false,
    },
    {
      name: "±1 SD",
      type: "line",
      data: errorBarData,
      color: t.inkSoft,
      lineWidth: 2.5,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
    },
  ],
});
