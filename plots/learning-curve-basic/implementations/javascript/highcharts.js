// anyplot.ai
// learning-curve-basic: Model Learning Curve
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Random-forest churn classifier: accuracy vs. training set size, 8-fold CV.
// Training score drifts down as the model can no longer memorize every fold;
// validation score climbs and the fold-to-fold spread narrows — the classic
// high-variance-shrinking-with-data signature.
const trainSizes = [50, 100, 200, 300, 400, 500, 700, 900, 1200, 1500];

const trainMean = [99, 98.5, 97.5, 96.8, 96.2, 95.8, 95.1, 94.6, 94.1, 93.8];
const trainStd = [0.8, 1.0, 0.9, 0.8, 0.7, 0.6, 0.6, 0.5, 0.5, 0.4];

const validationMean = [71, 76, 81, 84.5, 86.5, 87.8, 89.5, 90.5, 91.2, 91.7];
const validationStd = [5.5, 4.8, 3.8, 3.2, 2.8, 2.4, 2.0, 1.7, 1.5, 1.3];

const toPairs = (mean) => mean.map((m, i) => [trainSizes[i], m]);
const bandLower = (mean, std) =>
  mean.map((m, i) => [trainSizes[i], m - std[i]]);
const bandRange = (std) => std.map((s, i) => [trainSizes[i], 2 * s]);

const trainColor = t.palette[0];
const validationColor = t.palette[1];

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
    text: "learning-curve-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Validation accuracy converges toward training accuracy as the fold-to-fold variance narrows",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    type: "linear",
    tickPositions: trainSizes,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: {
      text: "Training Set Size",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
  },
  yAxis: {
    title: {
      text: "Accuracy (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    labels: {
      format: "{value}%",
      style: { color: t.inkSoft, fontSize: "14px" },
    },
    gridLineColor: t.grid,
    min: 60,
    max: 100,
    reversedStacks: false,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { valueSuffix: "%" },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    // Confidence bands: a transparent base area stacked with a translucent
    // range area — the classic Highcharts-core technique for a min/max band
    // without the arearange series type (which lives in highcharts-more).
    {
      name: "Training band base",
      type: "area",
      data: bandLower(trainMean, trainStd),
      stacking: "normal",
      stack: "train-band",
      color: "transparent",
      lineWidth: 0,
      fillOpacity: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Training ± 1 SD",
      type: "area",
      data: bandRange(trainStd),
      stacking: "normal",
      stack: "train-band",
      color: Highcharts.color(trainColor).setOpacity(0.18).get(),
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Validation band base",
      type: "area",
      data: bandLower(validationMean, validationStd),
      stacking: "normal",
      stack: "validation-band",
      color: "transparent",
      lineWidth: 0,
      fillOpacity: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Validation ± 1 SD",
      type: "area",
      data: bandRange(validationStd),
      stacking: "normal",
      stack: "validation-band",
      color: Highcharts.color(validationColor).setOpacity(0.18).get(),
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Training score",
      type: "line",
      data: toPairs(trainMean),
      color: trainColor,
      lineWidth: 3,
      marker: { enabled: true, radius: 5 },
    },
    {
      name: "Validation score",
      type: "line",
      data: toPairs(validationMean),
      color: validationColor,
      lineWidth: 3,
      marker: { enabled: true, radius: 5 },
    },
  ],
});
