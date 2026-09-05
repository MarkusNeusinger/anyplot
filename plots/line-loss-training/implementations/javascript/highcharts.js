// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fixed-seed LCG so runs are reproducible without a browser RNG.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const epochs = 60;
const epochArray = [];
const trainLoss = [];
const valLoss = [];

for (let epoch = 1; epoch <= epochs; epoch++) {
  epochArray.push(epoch);
  const trainNoise = (lcgRandom() - 0.5) * 0.04;
  const valNoise = (lcgRandom() - 0.5) * 0.09;
  const trainValue = 0.15 + 2.1 * Math.exp(-epoch / 12) + trainNoise;
  // Validation loss tracks training early on, then overfits and creeps back up.
  const overfitTerm = epoch > 22 ? 0.0026 * Math.pow(epoch - 22, 1.35) : 0;
  const valValue = 0.28 + 2.3 * Math.exp(-epoch / 13) + overfitTerm + valNoise;
  trainLoss.push(Math.max(0.05, Number(trainValue.toFixed(4))));
  valLoss.push(Math.max(0.08, Number(valValue.toFixed(4))));
}

let minValEpoch = 1;
let minValLoss = valLoss[0];
for (let i = 0; i < valLoss.length; i++) {
  if (valLoss[i] < minValLoss) {
    minValLoss = valLoss[i];
    minValEpoch = epochArray[i];
  }
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-loss-training · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Epoch", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 1,
    max: epochs,
    plotLines: [
      {
        value: minValEpoch,
        color: t.amber,
        width: 1.5,
        dashStyle: "Dash",
        zIndex: 3,
        label: {
          text: `Best epoch: ${minValEpoch}`,
          style: { color: t.inkSoft, fontSize: "13px" },
          y: 16,
        },
      },
    ],
  },
  yAxis: {
    title: { text: "Cross-Entropy Loss", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 0,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: {
      animation: false,
      marker: { enabled: false },
      lineWidth: 2.75,
    },
  },
  tooltip: { enabled: false },
  series: [
    {
      name: "Training loss",
      data: trainLoss,
      color: t.palette[0],
    },
    {
      name: "Validation loss",
      data: valLoss,
      color: t.palette[1],
    },
    {
      name: "Best epoch (min val. loss)",
      type: "scatter",
      data: [[minValEpoch, minValLoss]],
      color: t.amber,
      marker: { enabled: true, radius: 7, symbol: "circle", lineWidth: 1.5, lineColor: t.ink },
      enableMouseTracking: false,
    },
  ],
});
