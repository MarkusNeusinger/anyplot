// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

const epochCount = 60;
const epochs = Array.from({ length: epochCount }, (_, i) => i + 1);

const trainLoss = [];
const valLoss = [];
let minValLossEpoch = 1;
let minValLoss = Infinity;
for (let i = 0; i < epochCount; i++) {
  const epoch = i + 1;
  // Training loss: smooth exponential decay
  const train = 0.15 + 2.1 * Math.exp(-epoch / 12) + (rand() - 0.5) * 0.015;
  // Validation loss: tracks training loss early on, then plateaus and
  // creeps back up past ~epoch 30 to show overfitting
  const overfitOnset = 28;
  const overfitTerm = epoch > overfitOnset ? 0.0022 * (epoch - overfitOnset) ** 1.3 : 0;
  const val = 0.22 + 2.0 * Math.exp(-epoch / 13) + overfitTerm + (rand() - 0.5) * 0.02;

  trainLoss.push(Number(train.toFixed(4)));
  valLoss.push(Number(val.toFixed(4)));

  if (val < minValLoss) {
    minValLoss = val;
    minValLossEpoch = epoch;
  }
}

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: [t.palette[0], t.palette[1]],
  backgroundColor: "transparent",
  title: {
    text: "line-loss-training · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Training loss", "Validation loss"],
    top: 60,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemWidth: 24,
    itemHeight: 3,
  },
  grid: { left: 90, right: 60, top: 130, bottom: 80 },
  xAxis: {
    type: "value",
    name: "Epoch",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 1,
    max: epochCount,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Cross-Entropy Loss",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Training loss",
      type: "line",
      data: epochs.map((e, i) => [e, trainLoss[i]]),
      showSymbol: false,
      lineStyle: { width: 3.5, color: t.palette[0] },
    },
    {
      name: "Validation loss",
      type: "line",
      data: epochs.map((e, i) => [e, valLoss[i]]),
      showSymbol: false,
      lineStyle: { width: 3.5, color: t.palette[1] },
    },
    {
      name: "Optimal stopping point",
      type: "scatter",
      data: [[minValLossEpoch, minValLoss]],
      symbolSize: 16,
      itemStyle: {
        color: "transparent",
        borderColor: t.ink,
        borderWidth: 2.5,
      },
      z: 10,
      tooltip: { show: false },
      markLine: {
        symbol: "none",
        silent: true,
        lineStyle: { color: t.ink, type: "dashed", width: 1.5, opacity: 0.5 },
        label: {
          formatter: `Min val loss · epoch ${minValLossEpoch}`,
          color: t.inkSoft,
          fontSize: 13,
          position: "insideEndTop",
        },
        data: [{ xAxis: minValLossEpoch }],
      },
    },
  ],
});
