// anyplot.ai
// histogram-basic: Basic Histogram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Parcel delivery times (minutes) — right-skewed: most deliveries are quick,
// a long tail of delayed ones (Erlang-distributed via a fixed-seed LCG).
function makeLcg(seed) {
  let state = seed;
  return function random() {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const random = makeLcg(42);

const sampleCount = 400;
const deliveryTimes = [];
for (let i = 0; i < sampleCount; i++) {
  let erlangSum = 0;
  for (let j = 0; j < 3; j++) {
    erlangSum += -Math.log(random());
  }
  deliveryTimes.push(8 + erlangSum * 6);
}

const binCount = 22;
const minValue = Math.min(...deliveryTimes);
const maxValue = Math.max(...deliveryTimes);
const binWidth = (maxValue - minValue) / binCount;
const binCounts = new Array(binCount).fill(0);
deliveryTimes.forEach((value) => {
  const index = Math.min(
    Math.floor((value - minValue) / binWidth),
    binCount - 1,
  );
  binCounts[index]++;
});
const binLabels = binCounts.map((_, i) => Math.round(minValue + i * binWidth));

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "histogram-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 100, right: 60, top: 100, bottom: 110 },
  xAxis: {
    type: "category",
    data: binLabels,
    name: "Delivery Time (minutes)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: "auto" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    name: "Frequency",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "bar",
      data: binCounts,
      barCategoryGap: "0%",
      itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 1 },
    },
  ],
});
