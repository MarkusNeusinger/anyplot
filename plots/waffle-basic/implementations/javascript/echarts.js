// anyplot.ai
// waffle-basic: Basic Waffle Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Annual engineering-org budget allocation, in whole percentage points
// (sums to 100 — each of the 100 squares below represents exactly 1%).
const categories = [
  { name: "Product Development", value: 32 },
  { name: "Marketing", value: 24 },
  { name: "Sales Operations", value: 18 },
  { name: "Customer Support", value: 14 },
  { name: "Research & Development", value: 12 },
];

// Fill a 10x10 grid top-to-bottom, left-to-right, one cell per percentage
// point, in category order — the largest category anchors the top row.
const GRID = 10;
let cursor = 0;
const series = categories.map((cat, i) => {
  const points = [];
  for (let n = 0; n < cat.value; n += 1) {
    const col = cursor % GRID;
    const row = GRID - 1 - Math.floor(cursor / GRID);
    points.push([col, row]);
    cursor += 1;
  }
  const s = {
    name: `${cat.name} — ${cat.value}%`,
    type: "scatter",
    symbol: "rect",
    symbolSize: 72,
    data: points,
    itemStyle: {
      color: t.palette[i],
      borderColor: t.pageBg,
      borderWidth: 3,
    },
  };
  // Callout on the largest category's corner square, anchored via markPoint
  // so echarts positions it in data space rather than hand-computed pixels.
  if (i === 0) {
    s.markPoint = {
      symbol: "circle",
      symbolSize: 1,
      itemStyle: { color: "transparent", borderColor: "transparent" },
      label: {
        show: true,
        position: "top",
        distance: 50,
        color: t.ink,
        fontSize: 13,
        fontWeight: 600,
        formatter: `Largest share — ${cat.value}%`,
      },
      data: [{ coord: [0, GRID - 1] }],
    };
  }
  return s;
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "waffle-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    bottom: 16,
    left: "center",
    itemWidth: 16,
    itemHeight: 16,
    icon: "rect",
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemGap: 20,
  },
  grid: {
    top: 150,
    bottom: 150,
    left: 150,
    right: 150,
  },
  xAxis: {
    type: "value",
    min: -0.5,
    max: GRID - 0.5,
    interval: 1,
    show: false,
  },
  yAxis: {
    type: "value",
    min: -0.5,
    max: GRID - 0.5,
    interval: 1,
    show: false,
  },
  series,
});
