// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 83/100 | Created: 2026-07-25

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) --------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal(mean, std) {
  const u1 = lcg() || 1e-9;
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const groups = ["Edge Cache Hit", "Regional Cache", "Cold Start"];

const edgeCacheLatency = Array.from({ length: 140 }, () => randNormal(18, 3));
const regionalCacheLatency = Array.from({ length: 70 }, () =>
  randNormal(42, 6),
).concat(Array.from({ length: 70 }, () => randNormal(88, 8)));
const coldStartLatency = Array.from({ length: 90 }, () =>
  randNormal(230, 55),
);

const seriesData = [edgeCacheLatency, regionalCacheLatency, coldStartLatency];

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "rug-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 190, right: 60, top: 110, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Response Time (ms)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    data: groups,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: groups.map((name, i) => ({
    name,
    type: "scatter",
    data: seriesData[i].map((v) => [v, i]),
    symbol: "rect",
    symbolSize: [4, 130],
    itemStyle: { color: t.palette[i], opacity: 0.5 },
  })),
});
