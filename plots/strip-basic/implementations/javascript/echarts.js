// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 85/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG + Box-Muller) -----------------------
function makeRng(seed) {
  let state = seed;
  return function next() {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

function gaussian(rng) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const rng = makeRng(42);

const methods = [
  { name: "Lecture-Based", mean: 72, std: 9, n: 70 },
  { name: "Flipped Classroom", mean: 78, std: 7, n: 70 },
  { name: "Project-Based", mean: 81, std: 11, n: 70 },
  { name: "Blended", mean: 76, std: 8, n: 70 },
];

// Jitter width: fraction of the category band, spread as a pixel offset so
// points stay centered on the category tick without perturbing the x value.
const JITTER_PX = 90;

const categoryMeans = [];

const series = methods.map((method, i) => {
  const scores = Array.from({ length: method.n }, () => {
    const raw = method.mean + gaussian(rng) * method.std;
    return Math.round(Math.min(100, Math.max(0, raw)) * 10) / 10;
  });
  categoryMeans.push([method.name, scores.reduce((sum, s) => sum + s, 0) / scores.length]);

  return {
    name: method.name,
    type: "scatter",
    data: scores.map((score) => ({
      value: [method.name, score],
      symbolOffset: [(rng() - 0.5) * 2 * JITTER_PX, 0],
    })),
    symbolSize: 12,
    itemStyle: { color: t.palette[i], opacity: 0.6, borderColor: t.pageBg, borderWidth: 1 },
  };
});

// Group-mean reference line (spec Notes: "adding horizontal lines for group
// means... as reference"). A category axis snaps any fractional coordinate
// to its nearest integer index, so a markLine confined to one category's
// band is impossible via axis coords; instead draw it as a `custom` series
// with a pixel-space offset, exactly like the jitter above.
const meanLineSeries = {
  name: "Group Mean",
  type: "custom",
  silent: true,
  z: 5,
  data: categoryMeans,
  encode: { x: 0, y: 1 },
  renderItem: (params, api) => {
    const point = api.coord([api.value(0), api.value(1)]);
    return {
      type: "line",
      shape: {
        x1: point[0] - JITTER_PX,
        y1: point[1],
        x2: point[0] + JITTER_PX,
        y2: point[1],
      },
      style: { stroke: t.inkSoft, lineWidth: 2, lineDash: [6, 4] },
    };
  },
};

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "strip-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 100, right: 60, top: 100, bottom: 90 },
  xAxis: {
    type: "category",
    data: methods.map((m) => m.name),
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Exam Score (%)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 30,
    max: 100,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [...series, meanLineSeries],
});
