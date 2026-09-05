// anyplot.ai
// forest-basic: Meta-Analysis Forest Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Meta-analysis of randomized controlled trials: drug vs. placebo, risk ratio
// for the primary outcome. Null effect for a ratio measure is RR = 1.
const studies = [
  { label: "Chen 2015", effect: 0.72, ciLower: 0.55, ciUpper: 0.94, weight: 12 },
  { label: "Kumar 2016", effect: 0.85, ciLower: 0.68, ciUpper: 1.08, weight: 15 },
  { label: "Silva 2017", effect: 0.63, ciLower: 0.44, ciUpper: 0.9, weight: 9 },
  { label: "Fischer 2019", effect: 0.91, ciLower: 0.75, ciUpper: 1.12, weight: 18 },
  { label: "Tanaka 2020", effect: 0.77, ciLower: 0.6, ciUpper: 0.99, weight: 14 },
  { label: "Okafor 2021", effect: 0.68, ciLower: 0.5, ciUpper: 0.93, weight: 11 },
  { label: "Rossi 2022", effect: 0.8, ciLower: 0.64, ciUpper: 1.0, weight: 16 },
];
const pooledEstimate = { label: "Pooled Estimate", effect: 0.78, ciLower: 0.7, ciUpper: 0.87 };
const nullEffect = 1;

const weights = studies.map((s) => s.weight);
const minWeight = Math.min(...weights);
const maxWeight = Math.max(...weights);
const markerRadius = (weight) => 6 + ((weight - minWeight) / (maxWeight - minWeight)) * 10;

const rows = [...studies.map((s) => ({ ...s, pooled: false })), { ...pooledEstimate, pooled: true }];
const pooledIndex = rows.length - 1;

// --- Chart -------------------------------------------------------------------
const whiskerSeries = rows.map((row, index) => ({
  type: "line",
  data: [
    [index, row.ciLower],
    [index, row.ciUpper],
  ],
  color: Highcharts.color(row.pooled ? t.ink : t.palette[0])
    .setOpacity(0.55)
    .get(),
  lineWidth: row.pooled ? 3 : 2.5,
  marker: { enabled: false },
  enableMouseTracking: false,
  showInLegend: false,
  animation: false,
}));

const studySeries = {
  name: "Study estimate",
  type: "scatter",
  color: t.palette[0],
  data: studies.map((s, index) => ({ x: index, y: s.effect, marker: { radius: markerRadius(s.weight) } })),
  marker: { symbol: "circle", lineWidth: 1, lineColor: t.pageBg },
  zIndex: 5,
  animation: false,
};

const pooledSeries = {
  name: "Pooled estimate",
  type: "scatter",
  color: t.ink,
  data: [{ x: pooledIndex, y: pooledEstimate.effect, marker: { radius: 14 } }],
  marker: { symbol: "diamond", lineWidth: 1, lineColor: t.pageBg },
  zIndex: 6,
  animation: false,
};

Highcharts.chart("container", {
  chart: {
    inverted: true,
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "forest-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: rows.map((row) => row.label),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: 0.4,
    max: 1.2,
    tickInterval: 0.1,
    title: { text: "Risk Ratio", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: nullEffect,
        color: t.inkSoft,
        dashStyle: "Dash",
        width: 2,
        zIndex: 4,
        label: {
          text: "No effect (RR = 1)",
          rotation: 0,
          align: "right",
          verticalAlign: "top",
          x: -8,
          y: 20,
          style: { color: t.inkSoft, fontSize: "13px" },
        },
      },
    ],
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
  },
  series: [...whiskerSeries, studySeries, pooledSeries],
});
