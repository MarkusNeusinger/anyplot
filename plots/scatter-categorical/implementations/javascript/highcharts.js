// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
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

const rng = makeLcg(42);

const tiers = [
  { name: "Basic", engagement: 30, spend: 25, spread: 8, symbol: "circle" },
  { name: "Pro", engagement: 55, spend: 65, spread: 9, symbol: "diamond" },
  { name: "Enterprise", engagement: 78, spend: 140, spread: 10, symbol: "triangle" },
];

const series = tiers.map((tier, i) => {
  const data = [];
  for (let j = 0; j < 60; j += 1) {
    const engagement = tier.engagement + gaussian(rng) * 9;
    const spend = tier.spend + engagement * 0.6 + gaussian(rng) * tier.spread;
    data.push([Math.round(engagement * 10) / 10, Math.round(spend * 10) / 10]);
  }
  return {
    name: tier.name,
    data,
    color: t.palette[i],
    marker: { symbol: tier.symbol, radius: 6, lineWidth: 1, lineColor: t.pageBg },
  };
});

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
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Engagement Score", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 1,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Monthly Spend ($)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    title: { text: "Subscription Tier", style: { color: t.ink, fontSize: "14px" } },
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: { opacity: 0.75, states: { hover: { enabled: true } } },
  },
  series,
});
