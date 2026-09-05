// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) -----------------------------------
function makeLcg(seed) {
  let state = seed;
  return function lcg() {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function gaussian(rng) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Ordinary least-squares fit, used to draw a per-tier trend overlay.
function linearFit(points) {
  const n = points.length;
  const sumX = points.reduce((acc, [x]) => acc + x, 0);
  const sumY = points.reduce((acc, [, y]) => acc + y, 0);
  const sumXY = points.reduce((acc, [x, y]) => acc + x * y, 0);
  const sumXX = points.reduce((acc, [x]) => acc + x * x, 0);
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

const rng = makeLcg(42);

const tiers = [
  { name: "Basic", engagement: 30, spend: 25, spread: 8, symbol: "circle" },
  { name: "Pro", engagement: 55, spend: 65, spread: 9, symbol: "diamond" },
  { name: "Enterprise", engagement: 78, spend: 140, spread: 10, symbol: "triangle" },
];

const scatterSeries = tiers.map((tier, i) => {
  const data = [];
  for (let j = 0; j < 60; j += 1) {
    const engagement = tier.engagement + gaussian(rng) * 9;
    const spend = tier.spend + engagement * 0.6 + gaussian(rng) * tier.spread;
    data.push([Math.round(engagement * 10) / 10, Math.round(spend * 10) / 10]);
  }
  return {
    type: "scatter",
    name: tier.name,
    data,
    color: t.palette[i],
    marker: { symbol: tier.symbol, radius: 5, lineWidth: 1, lineColor: t.pageBg },
  };
});

// Trend overlay: one thin dashed regression line per tier, sharing its
// series color — a genuine per-group fit, not a decorative flourish.
const trendSeries = scatterSeries.map((s) => {
  const xs = s.data.map((p) => p[0]);
  const { slope, intercept } = linearFit(s.data);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  return {
    type: "line",
    name: `${s.name} trend`,
    data: [
      [xMin, slope * xMin + intercept],
      [xMax, slope * xMax + intercept],
    ],
    color: s.color,
    lineWidth: 2,
    dashStyle: "ShortDash",
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
  };
});

const series = [...scatterSeries, ...trendSeries];

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "scatter-categorical · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "700" },
  },
  xAxis: {
    title: { text: "Engagement Score", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Monthly Spend ($)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickLength: 0,
    gridLineWidth: 1,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    title: {
      text: "Subscription Tier",
      style: { color: t.ink, fontSize: "14px", fontWeight: "400" },
    },
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: { opacity: 0.65, states: { hover: { enabled: true } } },
  },
  series,
});
