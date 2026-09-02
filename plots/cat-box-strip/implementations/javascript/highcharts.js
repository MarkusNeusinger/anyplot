// anyplot.ai
// cat-box-strip: Box Plot with Strip Overlay
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Commute time (minutes) by transportation mode. Sample sizes differ across
// groups on purpose (comparing groups with sample size awareness).
function lcg(seed) {
  let state = seed;
  return function () {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function quantile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

const groups = [
  { name: "Car", n: 80, mean: 28, std: 6 },
  { name: "Bus", n: 65, mean: 42, std: 10 },
  { name: "Bike", n: 50, mean: 22, std: 5 },
  { name: "Walk", n: 35, mean: 48, std: 8 },
];
const categories = groups.map((g) => g.name);

const samples = groups.map((g) => {
  const values = [];
  for (let i = 0; i < g.n; i++) {
    values.push(Math.max(4, Math.round(g.mean + g.std * randNormal())));
  }
  return values;
});
// A couple of delayed-bus outliers, kept alongside the full box context.
samples[1].push(95, 91);

const stats = samples.map((values) => {
  const sorted = [...values].sort((a, b) => a - b);
  const q1 = quantile(sorted, 0.25);
  const median = quantile(sorted, 0.5);
  const q3 = quantile(sorted, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const inFence = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  return {
    q1,
    median,
    q3,
    whiskerLow: inFence[0],
    whiskerHigh: inFence[inFence.length - 1],
  };
});

// --- Box + whiskers, drawn with the core SVG renderer -----------------------
// highcharts-more (boxplot/errorbar series) isn't loaded in this bundle, so
// the box and whiskers are built from primitive shapes anchored to real axis
// coordinates, using the actual quartile/whisker statistics computed above.
function drawBoxes(chart) {
  const xAxis = chart.xAxis[0];
  const yAxis = chart.yAxis[0];
  const categoryPx = xAxis.toPixels(1) - xAxis.toPixels(0);
  const halfWidth = categoryPx * 0.22;

  stats.forEach((s, i) => {
    const color = t.palette[i % t.palette.length];
    const cx = xAxis.toPixels(i);
    const q1Y = yAxis.toPixels(s.q1);
    const q3Y = yAxis.toPixels(s.q3);
    const medianY = yAxis.toPixels(s.median);
    const lowY = yAxis.toPixels(s.whiskerLow);
    const highY = yAxis.toPixels(s.whiskerHigh);

    chart.renderer
      .path(["M", cx, highY, "L", cx, q3Y])
      .attr({ "stroke-width": 2, stroke: t.inkSoft, zIndex: 2 })
      .add();
    chart.renderer
      .path(["M", cx, q1Y, "L", cx, lowY])
      .attr({ "stroke-width": 2, stroke: t.inkSoft, zIndex: 2 })
      .add();
    chart.renderer
      .path(["M", cx - halfWidth, highY, "L", cx + halfWidth, highY])
      .attr({ "stroke-width": 2, stroke: t.inkSoft, zIndex: 2 })
      .add();
    chart.renderer
      .path(["M", cx - halfWidth, lowY, "L", cx + halfWidth, lowY])
      .attr({ "stroke-width": 2, stroke: t.inkSoft, zIndex: 2 })
      .add();
    chart.renderer
      .rect(cx - halfWidth, Math.min(q1Y, q3Y), halfWidth * 2, Math.abs(q1Y - q3Y))
      .attr({
        fill: color,
        "fill-opacity": 0.16,
        stroke: color,
        "stroke-width": 2.5,
        zIndex: 3,
      })
      .add();
    chart.renderer
      .path(["M", cx - halfWidth, medianY, "L", cx + halfWidth, medianY])
      .attr({ "stroke-width": 3, stroke: color, zIndex: 4 })
      .add();
  });
}

// --- Strip overlay (jittered scatter, drawn above the box) ------------------
const stripSeries = samples.map((values, i) => {
  const color = t.palette[i % t.palette.length];
  return {
    type: "scatter",
    name: categories[i],
    data: values.map((v) => [i + (rand() - 0.5) * 0.55, v]),
    color: color,
    marker: {
      radius: 4.5,
      lineWidth: 0,
      fillColor: Highcharts.color(color).setOpacity(0.55).get("rgba"),
    },
    zIndex: 5,
    showInLegend: false,
    states: { hover: { enabled: false } },
  };
});

// --- Chart --------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      load: function () {
        drawBoxes(this);
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "cat-box-strip · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: categories,
    min: -0.5,
    max: categories.length - 0.5,
    tickPositions: categories.map((_, i) => i),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: {
      text: "Transportation Mode",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
  },
  yAxis: {
    title: {
      text: "Commute Time (minutes)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: {
    pointFormat: "Commute: <b>{point.y:.0f} min</b>",
  },
  plotOptions: {
    series: { animation: false },
  },
  series: stripSeries,
});
