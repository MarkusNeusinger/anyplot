// anyplot.ai
// box-basic: Basic Box Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-24

// The core bundle (no highcharts-more) has no "boxplot" series type, so the box
// is built from two stacked "column" series (an invisible floor up to Q1, then
// a visible box from Q1 to Q3, colorByPoint from the Imprint palette). Whiskers
// and the median are drawn as two extra core "line" series (null-separated
// segments, one per category) rather than custom chart.renderer shapes — this
// Highcharts build paints renderer.path() additions behind the column bars
// they overlap, but a normal series defined after the box series always layers
// on top, which is what a median mark sitting inside the box needs.
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal(mean, std) {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}
function quartile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}
function boxStats(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const q1 = quartile(sorted, 0.25);
  const median = quartile(sorted, 0.5);
  const q3 = quartile(sorted, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const inRange = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  return {
    q1,
    median,
    q3,
    whiskerLow: inRange[0],
    whiskerHigh: inRange[inRange.length - 1],
    outliers: sorted.filter((v) => v < lowerFence || v > upperFence),
  };
}

const classes = [
  { name: "Algebra I", mean: 78, std: 9, n: 65 },
  { name: "Geometry", mean: 74, std: 11, n: 72 },
  { name: "Algebra II", mean: 81, std: 7, n: 58 },
  { name: "Precalculus", mean: 71, std: 13, n: 80 },
  { name: "Calculus", mean: 85, std: 8, n: 54 },
];
const categories = classes.map((c) => c.name);
const stats = {};
classes.forEach((c) => {
  const scores = Array.from({ length: c.n }, () =>
    Math.min(100, Math.max(0, randNormal(c.mean, c.std)))
  );
  stats[c.name] = boxStats(scores);
});

// Zoom the axis to the data's actual spread instead of forcing a 0 baseline —
// the stacked-column technique below still stacks from a true 0 threshold
// internally, so this only crops the (invisible) empty space beneath it.
const allBounds = classes.flatMap((c) => [
  stats[c.name].whiskerLow,
  stats[c.name].whiskerHigh,
  ...stats[c.name].outliers,
]);
const yMin = Math.max(0, Math.floor((Math.min(...allBounds) - 5) / 5) * 5);
const yMax = Math.min(100, Math.ceil((Math.max(...allBounds) + 5) / 5) * 5);

// Whiskers (box edge → fence) and caps, one null-separated "line" series for
// every category so a single series draws all the disconnected segments.
// Every entry (including gaps) carries an explicit x so a mixed array of real
// points and null-y gap markers can't be re-bucketed by an auto pointStart/
// pointInterval index — only the y:null gaps break the connecting line.
const capHalf = 0.13;
const whiskerData = categories.flatMap((c, i) => {
  const s = stats[c];
  return [
    { x: i, y: s.q3 }, { x: i, y: s.whiskerHigh }, { x: i, y: null },
    { x: i - capHalf, y: s.whiskerHigh }, { x: i + capHalf, y: s.whiskerHigh }, { x: i, y: null },
    { x: i, y: s.q1 }, { x: i, y: s.whiskerLow }, { x: i, y: null },
    { x: i - capHalf, y: s.whiskerLow }, { x: i + capHalf, y: s.whiskerLow }, { x: i, y: null },
  ];
});
// Median line spans the same half-width as the box itself (matches the
// pointPadding/groupPadding below), drawn as its own series so it renders on
// top of the box fill instead of being covered by it.
const boxHalf = 0.24;
const medianData = categories.flatMap((c, i) => [
  { x: i - boxHalf, y: stats[c].median },
  { x: i + boxHalf, y: stats[c].median },
  { x: i, y: null },
]);

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
    text: "box-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Class", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: yMin,
    max: yMax,
    reversedStacks: false, // keep series[0] (invisible floor) at the bottom of the stack
    title: { text: "Final Exam Score (%)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: { outside: false },
  plotOptions: {
    column: {
      stacking: "normal",
      pointPadding: 0.12,
      groupPadding: 0.18,
      borderRadius: 0,
      animation: false,
    },
    series: { animation: false },
  },
  series: [
    {
      name: "Floor",
      data: categories.map((c) => +stats[c].q1.toFixed(2)),
      color: "transparent",
      borderWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Interquartile range",
      data: categories.map((c) => +(stats[c].q3 - stats[c].q1).toFixed(2)),
      colorByPoint: true,
      borderColor: t.ink,
      borderWidth: 1.5,
      showInLegend: false,
      tooltip: {
        pointFormatter: function () {
          const s = stats[categories[this.index]];
          return (
            `<b>${categories[this.index]}</b><br/>` +
            `Max: ${s.whiskerHigh.toFixed(1)}<br/>Q3: ${s.q3.toFixed(1)}<br/>` +
            `Median: ${s.median.toFixed(1)}<br/>Q1: ${s.q1.toFixed(1)}<br/>` +
            `Min: ${s.whiskerLow.toFixed(1)}`
          );
        },
      },
    },
    {
      type: "line",
      name: "Whiskers",
      data: whiskerData,
      color: t.inkSoft,
      lineWidth: 1.75,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      type: "line",
      name: "Median",
      data: medianData,
      color: t.pageBg,
      lineWidth: 3,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      type: "scatter",
      name: "Outliers",
      data: classes.flatMap((c, i) =>
        stats[c.name].outliers.map((value) => ({
          x: i,
          y: +value.toFixed(1),
          color: t.palette[i % t.palette.length],
        }))
      ),
      marker: { radius: 5, symbol: "circle", lineWidth: 1.5, lineColor: t.pageBg },
      showInLegend: false,
      tooltip: { pointFormat: "Outlier: <b>{point.y:.1f}</b>" },
    },
  ],
});
