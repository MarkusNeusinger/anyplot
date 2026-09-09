// anyplot.ai
// shap-waterfall: SHAP Waterfall Plot for Feature Attribution
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Credit-risk model: SHAP contributions to the predicted probability of default
// for a single loan applicant, ordered by absolute contribution magnitude.
const baseValue = 0.18; // E[f(x)] — mean predicted default probability across training data
const features = [
  "Credit Score",
  "Debt-to-Income Ratio",
  "Payment History",
  "Credit Utilization",
  "Annual Income",
  "Recent Credit Inquiries",
  "Loan Amount",
  "Employment Length",
  "Number of Open Accounts",
  "Age of Credit History",
];
const shapValues = [-0.086, 0.052, -0.041, 0.033, -0.027, 0.021, 0.018, -0.014, 0.011, -0.009];

let running = baseValue;
const segments = shapValues.map((shap) => {
  const start = running;
  const end = start + shap;
  running = end;
  return { low: Math.min(start, end), high: Math.max(start, end), start, end, shap };
});
const finalValue = running;

const positiveColor = t.palette[4]; // matte red — pushes predicted risk up
const negativeColor = t.palette[2]; // blue — pushes predicted risk down

// --- Chart -------------------------------------------------------------------
const chart = Highcharts.chart("container", {
  chart: {
    type: "bar",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    spacingRight: 40,
  },
  credits: { enabled: false },
  title: {
    text: "shap-waterfall · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: features,
    reversed: true,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Contribution to Predicted Default Probability",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return `${Math.round(this.value * 100)}%`;
      },
    },
    plotLines: [
      {
        value: baseValue,
        color: t.inkSoft,
        width: 1.5,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `Base value: ${(baseValue * 100).toFixed(1)}%`,
          style: { color: t.inkSoft, fontSize: "13px" },
          rotation: 0,
          y: -8,
        },
      },
      {
        value: finalValue,
        color: t.ink,
        width: 2,
        dashStyle: "Solid",
        zIndex: 5,
        label: {
          text: `Prediction: ${(finalValue * 100).toFixed(1)}%`,
          style: { color: t.ink, fontSize: "13px", fontWeight: "600" },
          rotation: 0,
          y: -8,
          align: "right",
        },
      },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false, pointPadding: 0.15, groupPadding: 0, stacking: "normal" },
    bar: { borderWidth: 0 },
  },
  series: [
    {
      // Highcharts stacks bar/column series in reverse declaration order (the
      // first series lands on TOP of the stack) — declare the visible segment
      // first so it occupies [low, high], and the invisible spacer last so it
      // occupies [0, low] and pushes the visible segment into position.
      name: "SHAP contribution",
      data: segments.map((s) => ({
        y: s.high - s.low,
        color: s.shap >= 0 ? positiveColor : negativeColor,
        custom: { shap: s.shap },
      })),
      showInLegend: false,
      dataLabels: {
        enabled: true,
        inside: false,
        crop: false,
        overflow: "allow",
        style: { color: t.ink, fontSize: "13px", fontWeight: "500", textOutline: "none" },
        formatter() {
          const pp = this.point.custom.shap * 100;
          return `${pp >= 0 ? "+" : ""}${pp.toFixed(1)} pp`;
        },
      },
    },
    {
      name: "base",
      data: segments.map((s) => s.low),
      color: "rgba(0,0,0,0)",
      enableMouseTracking: false,
      showInLegend: false,
      dataLabels: { enabled: false },
    },
    {
      name: "Increases risk",
      data: [],
      color: positiveColor,
      showInLegend: true,
    },
    {
      name: "Decreases risk",
      data: [],
      color: negativeColor,
      showInLegend: true,
    },
  ],
});

// --- Connector lines between cumulative segments -----------------------------
const catAxis = chart.xAxis[0];
const valAxis = chart.yAxis[0];
const half = 0.5 - 0.15; // matches plotOptions.series.pointPadding
segments.slice(0, -1).forEach((seg, i) => {
  const xPixel = valAxis.toPixels(seg.end, false);
  const y1 = catAxis.toPixels(i + half, false);
  const y2 = catAxis.toPixels(i + 1 - half, false);
  chart.renderer
    .path(["M", xPixel, y1, "L", xPixel, y2])
    .attr({ stroke: t.inkSoft, "stroke-width": 1, dashstyle: "Dash", zIndex: 4 })
    .add();
});
