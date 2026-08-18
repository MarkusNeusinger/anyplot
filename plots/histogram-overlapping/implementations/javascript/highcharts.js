// anyplot.ai
// histogram-overlapping: Overlapping Histograms
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-18
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
  xAxis: {
    title: { text: "Reaction Time (ms)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: binStart,
    max: binEnd,
  },
  yAxis: {
    title: { text: "Number of Trials", style: { color: t.inkSoft, fontSize: "16px" } },
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
      pointRange: binWidth,
    },
    series: { animation: false },
  },
  series: [
    {
      name: "Control group",
      data: controlBins,
      color: Highcharts.color(t.palette[0]).setOpacity(0.55).get(),
    },
    {
      name: "Treatment group",
      data: treatmentBins,
      color: Highcharts.color(t.palette[1]).setOpacity(0.55).get(),
    },
  ],
});
