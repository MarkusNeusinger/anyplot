// anyplot.ai
// bump-basic: Basic Bump Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fictional racing championship: rank (1 = best) per team across 8 races.
// Each race column is a valid permutation of 1..8 — no ties.
const races = [
  "Race 1", "Race 2", "Race 3", "Race 4",
  "Race 5", "Race 6", "Race 7", "Race 8",
];

const teams = [
  { name: "Nova Racing", ranks: [3, 2, 1, 1, 1, 1, 1, 1] },
  { name: "Apex Motors", ranks: [5, 4, 3, 2, 2, 2, 2, 2] },
  { name: "Ironclad Racing", ranks: [8, 7, 6, 5, 4, 3, 3, 3] },
  { name: "Vector GP", ranks: [1, 1, 2, 3, 3, 4, 4, 4] },
  { name: "Vertex Motorsport", ranks: [6, 6, 7, 7, 8, 6, 5, 5] },
  { name: "Solstice Team", ranks: [7, 8, 8, 8, 7, 8, 7, 6] },
  { name: "Meridian F1", ranks: [4, 5, 5, 4, 5, 5, 6, 7] },
  { name: "Skyline Racing", ranks: [2, 3, 4, 6, 6, 7, 8, 8] },
];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bump-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  tooltip: { trigger: "axis" },
  grid: { left: 70, right: 210, top: 100, bottom: 80, containLabel: true },
  xAxis: {
    type: "category",
    data: races,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    inverse: true,
    min: 1,
    max: teams.length,
    interval: 1,
    name: "Rank (1 = best)",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: teams.map((team, i) => ({
    name: team.name,
    type: "line",
    data: team.ranks,
    color: t.palette[i],
    symbol: "circle",
    symbolSize: 14,
    lineStyle: { width: 3.5 },
    itemStyle: { color: t.palette[i] },
    emphasis: { focus: "series" },
    endLabel: {
      show: true,
      formatter: "{a}",
      color: t.ink,
      fontSize: 14,
      distance: 12,
    },
  })),
});
