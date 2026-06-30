// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-30

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Data — Employee satisfaction scores (0–10) before/after a workplace wellness initiative
const departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Legal", "Product"];
const scoreBefore = [6.2, 5.8, 6.5, 7.1, 5.4, 6.8, 6.0, 6.9];
const scoreAfter  = [7.7, 7.4, 8.0, 8.3, 7.0, 8.2, 7.3, 8.4];

// Sort ascending by improvement so the largest improvement appears at top
const sortIdx = departments.map((_, i) => i)
  .sort((a, b) => (scoreAfter[a] - scoreBefore[a]) - (scoreAfter[b] - scoreBefore[b]));
const labels  = sortIdx.map(i => departments[i]);
const vBefore = sortIdx.map(i => scoreBefore[i]);
const vAfter  = sortIdx.map(i => scoreAfter[i]);
const n       = labels.length;

// [score, categoryIndex] pairs — x = score, y = integer row index
const afterData  = vAfter.map((v,  i) => [v, i]);
const beforeData = vBefore.map((v, i) => [v, i]);

const chart = Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginLeft: 160,
    marginRight: 50,
    marginTop: 90,
    marginBottom: 70,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "dumbbell-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Employee satisfaction before/after workplace wellness initiative",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Satisfaction Score (0–10)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    min: 4.5,
    max: 9.5,
    tickInterval: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: null },
    min: -0.5,
    max: n - 0.5,
    tickPositions: labels.map((_, i) => i),
    labels: {
      formatter() { return labels[this.value] || ""; },
      style: { color: t.inkSoft, fontSize: "14px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: "transparent",
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 9, lineWidth: 0 },
    },
  },
  series: [
    {
      name: "After",
      data: afterData,
      color: t.palette[0],
      marker: { symbol: "circle" },
      zIndex: 5,
    },
    {
      name: "Before",
      data: beforeData,
      color: t.palette[1],
      marker: { symbol: "circle" },
      zIndex: 5,
    },
  ],
});

// Draw connecting lines between Before and After dots via the SVG renderer
const renderer = chart.renderer;
const plotLeft  = chart.plotLeft;
const plotTop   = chart.plotTop;

// Build a lookup from category index → before-series point
const beforeByIdx = {};
chart.series[1].data.forEach(p => { beforeByIdx[p.y] = p; });

chart.series[0].data.forEach((afterPt) => {
  const beforePt = beforeByIdx[afterPt.y];
  if (!beforePt) return;
  renderer.path([
    "M", plotLeft + beforePt.plotX, plotTop + beforePt.plotY,
    "L", plotLeft + afterPt.plotX,  plotTop + afterPt.plotY,
  ])
    .attr({ stroke: t.inkSoft, "stroke-width": 2.5, "stroke-opacity": 0.35 })
    .add();
});
