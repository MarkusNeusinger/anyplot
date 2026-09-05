// anyplot.ai
// roc-curve: ROC Curve with AUC
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Two diagnostic tests for detecting a disease, evaluated across classifier
// thresholds. tpr = fpr^(1/power) is concave and bows toward the top-left
// corner for power > 1, mimicking a real ROC curve shape.
const numPoints = 101;
const falsePositiveRates = Array.from({ length: numPoints }, (_, i) => i / (numPoints - 1));

const rocCurve = (power) => falsePositiveRates.map((fpr) => Math.pow(fpr, 1 / power));

const areaUnderCurve = (tprValues) => {
  let area = 0;
  for (let i = 1; i < falsePositiveRates.length; i += 1) {
    const dx = falsePositiveRates[i] - falsePositiveRates[i - 1];
    area += (dx * (tprValues[i] + tprValues[i - 1])) / 2;
  }
  return area;
};

const antibodyTestTpr = rocCurve(9);
const enzymeTestTpr = rocCurve(4);
const antibodyTestAuc = areaUnderCurve(antibodyTestTpr);
const enzymeTestAuc = areaUnderCurve(enzymeTestTpr);

const toPoints = (tprValues) =>
  falsePositiveRates.map((fpr, i) => [fpr, tprValues[i]]);

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
    text: "roc-curve · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "False Positive Rate", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    max: 1,
    tickInterval: 0.2,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "True Positive Rate", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    max: 1,
    tickInterval: 0.2,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    verticalAlign: "bottom",
  },
  tooltip: {
    valueDecimals: 2,
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    {
      name: `Antibody test (AUC = ${antibodyTestAuc.toFixed(2)})`,
      data: toPoints(antibodyTestTpr),
      color: t.palette[0],
      lineWidth: 3,
    },
    {
      name: `Enzyme test (AUC = ${enzymeTestAuc.toFixed(2)})`,
      data: toPoints(enzymeTestTpr),
      color: t.palette[1],
      lineWidth: 3,
    },
    {
      name: "Random classifier (AUC = 0.50)",
      data: [
        [0, 0],
        [1, 1],
      ],
      color: t.ink,
      dashStyle: "Dash",
      lineWidth: 2,
      enableMouseTracking: false,
    },
  ],
});
