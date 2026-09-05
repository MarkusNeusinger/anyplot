// anyplot.ai
// line-confidence: Line Plot with Confidence Interval
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Regression fit of crop yield against fertilizer application rate. The 95%
// confidence band follows the classic prediction-interval shape: narrowest
// near the mean of x (most data support) and widening toward both extremes,
// unlike a forecast band that only widens in one direction over time.
let seed = 7;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const rateStep = 5; // kg/ha
const rateMean = 100; // kg/ha, center of the sampled range
const lowerBase = []; // invisible stack base = y_lower
const bandHeight = []; // stacked on top of lowerBase to reach y_upper
const centerLine = []; // fitted trend

for (let rate = 0; rate <= 200; rate += rateStep) {
  const fit = 2.8 + 6.2 * (1 - Math.exp(-rate / 70)); // diminishing-returns fit
  const wobble = (nextRandom() - 0.5) * 0.15; // small residual scatter
  const center = fit + wobble;
  const se = 0.15 + 0.00003 * (rate - rateMean) ** 2; // bowtie-shaped std. error
  const halfWidth = 1.96 * se; // 95% prediction interval

  lowerBase.push(Math.round((center - halfWidth) * 100) / 100);
  bandHeight.push(Math.round(halfWidth * 2 * 100) / 100);
  centerLine.push(Math.round(center * 100) / 100);
}

const rates = [];
for (let rate = 0; rate <= 200; rate += rateStep) rates.push(rate);

const bandFill = Highcharts.color(t.palette[0]).setOpacity(0.22).get();

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-confidence · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Crop yield vs. fertilizer application rate · regression fit with 95% confidence interval",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Fertilizer Application Rate (kg/ha)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    tickInterval: 25,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Predicted Crop Yield (t/ha)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    // The stacking trick anchors an invisible spacer series at 0, which would
    // otherwise force the axis to start at 0 and waste most of the canvas
    // below the ~2-9 t/ha data range. Cropping the visible min is safe: the
    // spacer stays fully transparent, so the stacking math is unaffected.
    min: 1.5,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { shared: true, valueSuffix: " t/ha" },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    // Stacking order matters: Highcharts stacks the FIRST series in this array
    // as the cumulative top of the stack, and the LAST as the base at 0. So the
    // visible band goes first (rendering from y_lower to y_upper) and the
    // invisible spacer goes second (rendering from 0 to y_lower, hidden).
    {
      name: "95% confidence interval",
      type: "area",
      data: rates.map((rate, i) => [rate, bandHeight[i]]),
      stacking: "normal",
      color: bandFill,
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: true,
    },
    {
      name: "Lower bound",
      type: "area",
      data: rates.map((rate, i) => [rate, lowerBase[i]]),
      stacking: "normal",
      color: "transparent",
      fillOpacity: 0,
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Predicted yield",
      type: "spline",
      data: rates.map((rate, i) => [rate, centerLine[i]]),
      color: t.palette[0],
      lineWidth: 3.5,
      showInLegend: true,
    },
  ],
});
