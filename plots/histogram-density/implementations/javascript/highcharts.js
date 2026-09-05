// anyplot.ai
// histogram-density: Density Histogram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// mulberry32 — small, dependency-free, seeded PRNG (Math.random() is not seeded).
function mulberry32(seed) {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let z = Math.imul(a ^ (a >>> 15), 1 | a);
    z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

// Box-Muller transform -> approximately normal samples.
function nextNormal(mean, sd) {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + sd * z;
}

const MEAN = 10.0; // target bolt diameter, mm
const SD = 0.05; // machining process variability, mm
const N = 600;
const diameters = Array.from({ length: N }, () => nextNormal(MEAN, SD));

// --- Histogram binning (density-normalized so total bar area = 1) ----------
const NUM_BINS = 24;
const dataMin = Math.min(...diameters);
const dataMax = Math.max(...diameters);
const binWidth = (dataMax - dataMin) / NUM_BINS;
const counts = new Array(NUM_BINS).fill(0);
diameters.forEach((value) => {
  const bin = Math.min(NUM_BINS - 1, Math.floor((value - dataMin) / binWidth));
  counts[bin] += 1;
});
const histogramData = counts.map((count, i) => {
  const center = dataMin + (i + 0.5) * binWidth;
  const density = count / (N * binWidth);
  return [center, density];
});

// --- Theoretical normal PDF overlay (goodness-of-fit reference) ------------
function normalPdf(x, mean, sd) {
  return (
    Math.exp(-0.5 * ((x - mean) / sd) ** 2) / (sd * Math.sqrt(2 * Math.PI))
  );
}
const CURVE_POINTS = 120;
const curveMin = MEAN - 4 * SD;
const curveMax = MEAN + 4 * SD;
const pdfCurve = Array.from({ length: CURVE_POINTS }, (_, i) => {
  const x = curveMin + (i / (CURVE_POINTS - 1)) * (curveMax - curveMin);
  return [x, normalPdf(x, MEAN, SD)];
});

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
    text: "histogram-density · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "linear",
    title: {
      text: "Bolt Diameter (mm)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      format: "{value:.2f}",
    },
  },
  yAxis: {
    title: { text: "Density", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { valueDecimals: 3 },
  plotOptions: {
    series: { animation: false },
    column: {
      pointRange: binWidth,
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 1,
      borderColor: t.pageBg,
    },
  },
  series: [
    {
      name: "Empirical density",
      type: "column",
      data: histogramData,
      color: t.palette[0],
    },
    {
      name: "Normal PDF (fit)",
      type: "spline",
      data: pdfCurve,
      color: t.ink,
      dashStyle: "Dash",
      lineWidth: 2.5,
      marker: { enabled: false },
      enableMouseTracking: false,
    },
  ],
});
