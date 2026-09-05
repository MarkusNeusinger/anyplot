// anyplot.ai
// forest-basic: Meta-Analysis Forest Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): meta-analysis of RCTs, treatment vs control on 30-day readmission
const studies = [
  { name: "Chen et al. (2015)", effect: 0.72, lower: 0.55, upper: 0.94, weight: 9.5 },
  { name: "Alvarez et al. (2016)", effect: 0.68, lower: 0.48, upper: 0.97, weight: 7.2 },
  { name: "Kowalski et al. (2017)", effect: 0.85, lower: 0.62, upper: 1.16, weight: 8.8 },
  { name: "Osei et al. (2018)", effect: 0.61, lower: 0.45, upper: 0.83, weight: 11.3 },
  { name: "Tanaka et al. (2019)", effect: 0.79, lower: 0.58, upper: 1.08, weight: 9.9 },
  { name: "Nguyen et al. (2020)", effect: 0.55, lower: 0.38, upper: 0.8, weight: 6.4 },
  { name: "Ferreira et al. (2021)", effect: 0.7, lower: 0.52, upper: 0.94, weight: 10.1 },
  { name: "Whitfield et al. (2022)", effect: 0.64, lower: 0.49, upper: 0.84, weight: 13.8 },
];
const pooled = { name: "Pooled Estimate", effect: 0.68, lower: 0.59, upper: 0.78, weight: 100 };

// Category axis places index 0 at the bottom; the pooled diamond anchors the
// bottom row, studies stack upward in chronological order (oldest on top).
const rows = [pooled, ...studies.slice().reverse()];
const categories = rows.map((row) => row.name);
const maxWeight = Math.max(...studies.map((row) => row.weight));

const seriesData = rows.map((row, index) => [
  row.effect,
  index,
  row.lower,
  row.upper,
  row.weight,
  row === pooled ? 1 : 0,
]);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Render: per-row whisker + point-estimate circle, pooled row a diamond
function renderItem(params, api) {
  const yIndex = api.value(1);
  const isPooled = api.value(5) === 1;
  const lowerPt = api.coord([api.value(2), yIndex]);
  const upperPt = api.coord([api.value(3), yIndex]);
  const pointPt = api.coord([api.value(0), yIndex]);
  const color = isPooled ? t.ink : t.palette[0];

  if (isPooled) {
    const halfHeight = 22;
    return {
      type: "polygon",
      shape: {
        points: [
          [pointPt[0], pointPt[1] - halfHeight],
          [upperPt[0], pointPt[1]],
          [pointPt[0], pointPt[1] + halfHeight],
          [lowerPt[0], pointPt[1]],
        ],
      },
      style: { fill: color, stroke: color },
    };
  }

  const radius = 8 + (api.value(4) / maxWeight) * 10;
  const capHalf = 7;
  return {
    type: "group",
    children: [
      {
        type: "line",
        shape: { x1: lowerPt[0], y1: lowerPt[1], x2: upperPt[0], y2: upperPt[1] },
        style: { stroke: color, lineWidth: 2.5 },
      },
      {
        type: "line",
        shape: { x1: lowerPt[0], y1: lowerPt[1] - capHalf, x2: lowerPt[0], y2: lowerPt[1] + capHalf },
        style: { stroke: color, lineWidth: 2.5 },
      },
      {
        type: "line",
        shape: { x1: upperPt[0], y1: upperPt[1] - capHalf, x2: upperPt[0], y2: upperPt[1] + capHalf },
        style: { stroke: color, lineWidth: 2.5 },
      },
      {
        type: "circle",
        shape: { cx: pointPt[0], cy: pointPt[1], r: radius },
        style: { fill: color },
      },
    ],
  };
}

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "forest-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 280, right: 110, top: 90, bottom: 90 },
  xAxis: {
    type: "value",
    min: 0.3,
    max: 1.5,
    name: "Odds Ratio (95% CI) — Treatment vs Control",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
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
      type: "custom",
      encode: { x: 0, y: 1 },
      data: seriesData,
      renderItem: renderItem,
      markLine: {
        symbol: "none",
        silent: true,
        label: { show: false },
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        data: [{ xAxis: 1 }],
      },
      z: 3,
    },
  ],
});
