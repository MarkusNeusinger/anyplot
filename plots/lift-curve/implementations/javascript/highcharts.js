//# anyplot-orientation: landscape
// anyplot.ai
// lift-curve: Model Lift Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: simulate a retention-campaign response model on 2000 customers --
// Deterministic PRNG (mulberry32) — the browser has no seeded Math.random.
function mulberry32(seed) {
  return function () {
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

const CUSTOMER_COUNT = 2000;
let totalResponders = 0;
const customers = [];
for (let i = 0; i < CUSTOMER_COUNT; i++) {
  // Most customers have low churn-retention-offer propensity; a few are highly likely to respond.
  const propensity = Math.pow(rand(), 4);
  const trueResponseProb = Math.min(0.9, propensity);
  const responded = rand() < trueResponseProb ? 1 : 0;
  totalResponders += responded;
  // The model score correlates with true propensity but is imperfect (added noise).
  const score = propensity + (rand() - 0.5) * 0.3;
  customers.push({ responded, score });
}
customers.sort((a, b) => b.score - a.score);

const baselineRate = totalResponders / CUSTOMER_COUNT;

const liftData = [];
let cumResponders = 0;
let cumCustomers = 0;
for (let pct = 1; pct <= 100; pct++) {
  const cutoff = Math.round((pct / 100) * CUSTOMER_COUNT);
  while (cumCustomers < cutoff) {
    cumResponders += customers[cumCustomers].responded;
    cumCustomers++;
  }
  const lift = cumResponders / cumCustomers / baselineRate;
  const isDecile = pct % 10 === 0;
  liftData.push({
    x: pct,
    y: Number(lift.toFixed(3)),
    marker: { enabled: isDecile, radius: isDecile ? 6 : 0 },
    dataLabels: { enabled: isDecile },
  });
}

const randomSelectionData = [
  { x: 0, y: 1 },
  { x: 100, y: 1 },
];

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
    text: "lift-curve · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: `Retention offer targeting · baseline response rate ${(baselineRate * 100).toFixed(1)}%`,
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Population Targeted (%)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    max: 100,
    tickInterval: 10,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}%" },
  },
  yAxis: {
    title: { text: "Cumulative Lift", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}x" },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    valueSuffix: "x lift",
  },
  plotOptions: {
    series: { animation: false },
    line: { lineWidth: 3, marker: { enabled: false } },
  },
  series: [
    {
      name: "Model",
      data: liftData,
      color: t.palette[0],
      zIndex: 2,
      dataLabels: {
        enabled: false,
        format: "{y:.1f}x",
        style: { color: t.ink, fontSize: "13px", fontWeight: "600", textOutline: "none" },
        y: -14,
      },
    },
    {
      name: "Random selection (no lift)",
      data: randomSelectionData,
      color: t.ink,
      dashStyle: "Dash",
      lineWidth: 2,
      marker: { enabled: false },
      enableMouseTracking: false,
      zIndex: 1,
    },
  ],
});
