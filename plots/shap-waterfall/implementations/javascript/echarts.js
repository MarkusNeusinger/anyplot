// anyplot.ai
// shap-waterfall: SHAP Waterfall Plot for Feature Attribution
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Credit-scoring model explaining one applicant's predicted default probability.
const baseValue = 0.32;
const finalValue = 0.385;
const featureContributions = [
  { feature: "Credit Score", shap: -0.22 },
  { feature: "Recent Late Payments", shap: 0.15 },
  { feature: "Debt-to-Income Ratio", shap: 0.11 },
  { feature: "Credit Utilization", shap: 0.08 },
  { feature: "Income", shap: -0.06 },
  { feature: "Employment Length", shap: -0.04 },
  { feature: "Loan Amount", shap: 0.03 },
  { feature: "Number of Open Accounts", shap: 0.02 },
  { feature: "Age", shap: -0.015 },
  { feature: "Existing Loans", shap: 0.01 },
];

// Smallest |SHAP| first so the largest contribution sits nearest the top,
// right below the final-prediction bar (categories plot bottom-to-top).
const orderedFeatures = [...featureContributions].sort(
  (a, b) => Math.abs(a.shap) - Math.abs(b.shap)
);

// Build the cumulative waterfall: each row knows the invisible "placeholder"
// offset it stacks on top of, its own visible bar length, and the running
// total once it has been applied (used to draw the connecting flow line).
const rows = [
  {
    name: "Base value",
    placeholder: 0,
    value: baseValue,
    after: baseValue,
    kind: "anchor",
    label: `Base: ${baseValue.toFixed(3)}`,
  },
];
let running = baseValue;
orderedFeatures.forEach(({ feature, shap }) => {
  const start = running;
  const end = running + shap;
  rows.push({
    name: feature,
    placeholder: Math.min(start, end),
    value: Math.abs(shap),
    after: end,
    kind: shap >= 0 ? "increase" : "decrease",
    label: `${shap >= 0 ? "+" : "−"}${Math.abs(shap).toFixed(3)}`,
  });
  running = end;
});
rows.push({
  name: "Final prediction",
  placeholder: 0,
  value: finalValue,
  after: finalValue,
  kind: "anchor",
  label: `Final: ${finalValue.toFixed(3)}`,
});

const categories = rows.map((r) => r.name);
const placeholderData = rows.map((r) => r.placeholder);
const increaseData = rows.map((r) => (r.kind === "increase" ? r.value : "-"));
const decreaseData = rows.map((r) => (r.kind === "decrease" ? r.value : "-"));
const anchorData = rows.map((r) => (r.kind === "anchor" ? r.value : "-"));
const flowData = rows.map((r) => r.after);

const barLabel = {
  show: true,
  position: "right",
  color: t.inkSoft,
  fontSize: 14,
  formatter: (params) => rows[params.dataIndex].label,
};

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "shap-waterfall · javascript · echarts · anyplot.ai",
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Increases prediction", "Decreases prediction", "Base / final value"],
    top: 60,
    left: "center",
    itemWidth: 16,
    itemHeight: 16,
    textStyle: { color: t.ink, fontSize: 15 },
  },
  grid: { left: 40, right: 150, top: 125, bottom: 70, containLabel: true },
  xAxis: {
    type: "value",
    min: 0,
    max: 0.75,
    name: "Predicted default probability",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => v.toFixed(2) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: categories,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      name: "placeholder",
      type: "bar",
      stack: "flow",
      silent: true,
      barWidth: 34,
      itemStyle: { color: "transparent" },
      data: placeholderData,
      tooltip: { show: false },
    },
    {
      name: "Increases prediction",
      type: "bar",
      stack: "flow",
      barWidth: 34,
      itemStyle: { color: t.palette[4] },
      label: barLabel,
      data: increaseData,
    },
    {
      name: "Decreases prediction",
      type: "bar",
      stack: "flow",
      barWidth: 34,
      itemStyle: { color: t.palette[2] },
      label: barLabel,
      data: decreaseData,
    },
    {
      name: "Base / final value",
      type: "bar",
      stack: "flow",
      barWidth: 34,
      itemStyle: { color: t.ink, opacity: 0.85 },
      label: barLabel,
      data: anchorData,
    },
    {
      name: "flow",
      type: "line",
      data: flowData,
      symbol: "none",
      silent: true,
      z: 3,
      lineStyle: { type: "dashed", width: 1.5, color: t.inkSoft, opacity: 0.55 },
      tooltip: { show: false },
    },
  ],
});
