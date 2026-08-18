// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-08-18
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG + Box-Muller) -----------------------
let seed = 42;
function nextUniform() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function nextNormal(mean, sd) {
  const u1 = Math.max(nextUniform(), 1e-9);
  const u2 = nextUniform();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}

const trialsPerGroup = 220;
const controlReactionTimes = Array.from({ length: trialsPerGroup }, () => nextNormal(480, 62));
const treatmentReactionTimes = Array.from({ length: trialsPerGroup }, () => nextNormal(428, 55));

// Shared bin edges so both distributions compare directly
const binWidth = 20;
const binStart = 260;
const binEnd = 660;

const buildHistogram = (values) => {
  const bins = [];
  for (let edge = binStart; edge < binEnd; edge += binWidth) {
    const count = values.filter((v) => v >= edge && v < edge + binWidth).length;
    bins.push([edge + binWidth / 2, count]);
  }
  return bins;
};

const controlBins = buildHistogram(controlReactionTimes);
const treatmentBins = buildHistogram(treatmentReactionTimes);

const mean = (values) => values.reduce((sum, v) => sum + v, 0) / values.length;
const controlMean = mean(controlReactionTimes);
const treatmentMean = mean(treatmentReactionTimes);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "histogram-overlapping · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: `n = ${trialsPerGroup} trials per group · treatment reacts ${Math.round(controlMean - treatmentMean)} ms faster on average`,
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Reaction Time (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineWidth: 1,
    lineColor: t.grid,
    tickColor: t.grid,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: binStart,
    max: binEnd,
    plotLines: [
      {
        value: controlMean,
        color: t.palette[0],
        width: 2,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `Control mean ${Math.round(controlMean)} ms`,
          style: { color: t.palette[0], fontSize: "12px", fontWeight: "600" },
          rotation: 0,
          align: "left",
          x: 4,
          y: 14,
        },
      },
      {
        value: treatmentMean,
        color: t.palette[1],
        width: 2,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `Treatment mean ${Math.round(treatmentMean)} ms`,
          style: { color: t.palette[1], fontSize: "12px", fontWeight: "600" },
          rotation: 0,
          align: "right",
          x: -4,
          y: 32,
        },
      },
    ],
  },
  yAxis: {
    title: { text: "Number of Trials", style: { color: t.inkSoft, fontSize: "16px" } },
    lineWidth: 0,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    column: {
      grouping: false,
      groupPadding: 0,
      pointPadding: 0,
      borderWidth: 0,
      borderRadius: 3,
      pointRange: binWidth,
    },
    series: { animation: false },
  },
  series: [
    {
      name: "Control group",
      data: controlBins,
      color: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, Highcharts.color(t.palette[0]).setOpacity(0.75).get()],
          [1, Highcharts.color(t.palette[0]).setOpacity(0.4).get()],
        ],
      },
    },
    {
      name: "Treatment group",
      data: treatmentBins,
      color: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, Highcharts.color(t.palette[1]).setOpacity(0.75).get()],
          [1, Highcharts.color(t.palette[1]).setOpacity(0.4).get()],
        ],
      },
    },
  ],
});
