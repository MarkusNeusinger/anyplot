// anyplot.ai
// line-stock-comparison: Stock Price Comparison Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Three clean-energy stocks plus a sector benchmark index, one trading year
// (2024), rebased to 100 at the first date so relative performance is
// directly comparable regardless of starting price.

const MS_PER_DAY = 86400000;

function tradingDays(year, count) {
  const days = [];
  let cursor = Date.UTC(year, 0, 2);
  while (days.length < count) {
    const weekday = new Date(cursor).getUTCDay();
    if (weekday !== 0 && weekday !== 6) days.push(cursor);
    cursor += MS_PER_DAY;
  }
  return days;
}

function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function priceWalk(seed, start, drift, volatility, n) {
  const rng = makeLcg(seed);
  const prices = [start];
  for (let i = 1; i < n; i++) {
    const shock = (rng() - 0.5) * 2 * volatility;
    prices.push(prices[i - 1] * (1 + drift + shock));
  }
  return prices;
}

const dates = tradingDays(2024, 252);

const stocks = [
  { name: "Solaris Power (SOLR)", seed: 11, start: 42, drift: 0.0009, vol: 0.018 },
  { name: "Windfield Energy (WNDF)", seed: 23, start: 58, drift: 0.0004, vol: 0.022 },
  { name: "HydroGen Corp (HYDR)", seed: 37, start: 76, drift: -0.0003, vol: 0.02 },
  { name: "Clean Energy Index (XCEI)", seed: 51, start: 100, drift: 0.0003, vol: 0.009 },
];

const series = stocks.map((s, i) => {
  const prices = priceWalk(s.seed, s.start, s.drift, s.vol, dates.length);
  const basePrice = prices[0];
  const isBenchmark = i === stocks.length - 1;
  return {
    name: s.name,
    data: prices.map((p, idx) => [dates[idx], (p / basePrice) * 100]),
    lineWidth: isBenchmark ? 2 : 2.75,
    dashStyle: isBenchmark ? "Dash" : "Solid",
  };
});

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
    text: "line-stock-comparison · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Trading Date (2024)", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    title: { text: "Rebased Price (Start = 100)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: 100,
        color: t.inkSoft,
        dashStyle: "Dash",
        width: 1.5,
        zIndex: 3,
        label: {
          text: "Start (100)",
          align: "right",
          x: -4,
          y: -6,
          style: { color: t.inkSoft, fontSize: "13px" },
        },
      },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { xDateFormat: "%b %e, %Y", valueDecimals: 1 },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series,
});
