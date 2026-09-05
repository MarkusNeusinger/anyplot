// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG so both theme renders draw identical points.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gaussian(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const species = [
  { name: "Sepal Iris", leafLength: 4.4, leafWidth: 1.2, n: 45 },
  { name: "Marsh Iris", leafLength: 5.6, leafWidth: 2.0, n: 45 },
  { name: "Alpine Iris", leafLength: 6.3, leafWidth: 2.4, n: 45 },
];

const series = species.map((sp, i) => ({
  name: sp.name,
  type: "scatter",
  symbolSize: 18,
  data: Array.from({ length: sp.n }, () => [
    Number(gaussian(sp.leafLength, 0.55).toFixed(2)),
    Number(gaussian(sp.leafWidth, 0.28).toFixed(2)),
  ]),
  // Theme-adaptive edge separates overlapping markers in the Marsh/Alpine
  // overlap band (5.5-6.5 cm); page-bg stroke reads as a halo, not chartjunk.
  itemStyle: { opacity: 0.72, borderColor: t.pageBg, borderWidth: 1 },
  emphasis: {
    focus: "series",
    itemStyle: { opacity: 1, borderColor: t.ink, borderWidth: 1.5 },
  },
  // Overlap-zone callout lives on the middle (Marsh Iris) series only.
  markArea:
    i === 1
      ? {
          silent: true,
          itemStyle: { color: t.inkSoft, opacity: 0.06 },
          label: { color: t.inkSoft, fontSize: 12, position: "insideBottom" },
          data: [
            [
              { xAxis: 5.5, name: "Overlap zone" },
              { xAxis: 6.5 },
            ],
          ],
        }
      : undefined,
}));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "scatter-categorical · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    top: 56,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 18,
    itemHeight: 12,
  },
  tooltip: {
    trigger: "item",
    formatter: (p) =>
      `${p.seriesName}<br/>Leaf Length: ${p.data[0]} cm<br/>Leaf Width: ${p.data[1]} cm`,
  },
  grid: { left: 90, right: 60, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Leaf Length (cm)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Leaf Width (cm)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series,
});
