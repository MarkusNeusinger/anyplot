// anyplot.ai
// histogram-stacked: Stacked Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG — no Math.random) -------------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function rng() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function randomNormal(rng) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function sampleWaitTimes(rng, mean, stdDev, count) {
  const samples = [];
  for (let i = 0; i < count; i++) {
    samples.push(Math.max(0.2, mean + stdDev * randomNormal(rng)));
  }
  return samples;
}

const rng = makeLcg(42);
const waitTimesDowntown = sampleWaitTimes(rng, 4.0, 1.4, 500);
const waitTimesUptown = sampleWaitTimes(rng, 6.5, 1.8, 500);
const waitTimesSuburban = sampleWaitTimes(rng, 9.0, 2.2, 500);

const allWaitTimes = [...waitTimesDowntown, ...waitTimesUptown, ...waitTimesSuburban];
const rangeMin = Math.min(...allWaitTimes);
const rangeMax = Math.max(...allWaitTimes);
const binCount = 14;
const binWidth = (rangeMax - rangeMin) / binCount;
const binLabels = Array.from({ length: binCount }, (_, i) => {
  const lo = rangeMin + i * binWidth;
  const hi = rangeMin + (i + 1) * binWidth;
  return `${lo.toFixed(1)}–${hi.toFixed(1)}`;
});

function binFrequencies(values) {
  const counts = new Array(binCount).fill(0);
  for (const value of values) {
    let idx = Math.floor((value - rangeMin) / binWidth);
    if (idx >= binCount) idx = binCount - 1;
    if (idx < 0) idx = 0;
    counts[idx]++;
  }
  return counts;
}

const frequenciesDowntown = binFrequencies(waitTimesDowntown);
const frequenciesUptown = binFrequencies(waitTimesUptown);
const frequenciesSuburban = binFrequencies(waitTimesSuburban);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "histogram-stacked · javascript · echarts · anyplot.ai",
    left: "center",
    top: 22,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Downtown", "Uptown", "Suburban"],
    top: 76,
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink },
    formatter: (params) => {
      const total = params.reduce((sum, p) => sum + p.value, 0);
      const lines = params.map((p) => `${p.marker} ${p.seriesName}: ${p.value}`);
      return `${params[0].axisValue}<br/>${lines.join("<br/>")}<br/><strong>Total: ${total}</strong>`;
    },
  },
  grid: { left: 100, right: 60, top: 150, bottom: 100 },
  xAxis: {
    type: "category",
    data: binLabels,
    name: "Wait Time (minutes)",
    nameLocation: "middle",
    nameGap: 54,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Frequency",
    nameLocation: "middle",
    nameGap: 64,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Downtown",
      type: "bar",
      stack: "total",
      data: frequenciesDowntown,
      itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 1 },
      emphasis: { focus: "series" },
      barCategoryGap: "0%",
    },
    {
      name: "Uptown",
      type: "bar",
      stack: "total",
      data: frequenciesUptown,
      itemStyle: { color: t.palette[1], borderColor: t.pageBg, borderWidth: 1 },
      emphasis: { focus: "series" },
    },
    {
      name: "Suburban",
      type: "bar",
      stack: "total",
      data: frequenciesSuburban,
      itemStyle: {
        color: t.palette[2],
        borderColor: t.pageBg,
        borderWidth: 1,
        borderRadius: [6, 6, 0, 0],
      },
      emphasis: { focus: "series" },
    },
  ],
});
