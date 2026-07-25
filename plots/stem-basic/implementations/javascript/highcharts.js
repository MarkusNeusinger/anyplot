// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data: damped discrete-time impulse response (signal processing) -------
const sampleCount = 40;
const samples = [];
for (let n = 0; n < sampleCount; n += 1) {
  const amplitude = Math.exp(-n / 14) * Math.cos(n * 0.45);
  samples.push({ x: n, y: Math.round(amplitude * 1000) / 1000 });
}
const peakIndex = samples.reduce((best, s, i) => (s.y > samples[best].y ? i : best), 0);
const peakLabel = {
  enabled: true,
  format: "Peak",
  y: -16,
  style: { color: t.ink, fontSize: "13px", fontWeight: "600", textOutline: "none" },
};

// --- Chart -------------------------------------------------------------
// Highcharts has no lollipop/stem series in the core bundle, so the stem is
// built from two aligned series: a thin column (baseline-to-value stem) and
// a scatter series (the marker) — a standard core-only combo technique.
// `negativeColor` (a distinctive core-Highcharts zone feature) splits every
// stem/marker by sign — brand green above zero, Imprint diverging blue below
// — and a dataLabel callout marks the peak sample to guide the eye into the
// decay story.
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
    text: "stem-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Sample Index (n)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: -0.5,
    max: sampleCount - 0.5,
  },
  yAxis: {
    title: { text: "Amplitude", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [{ value: 0, color: t.inkSoft, width: 1, zIndex: 2 }],
  },
  legend: { enabled: false },
  tooltip: { valueDecimals: 3 },
  plotOptions: {
    series: { animation: false, negativeColor: t.div[2] },
    column: { pointWidth: 3, pointPadding: 0, groupPadding: 0, borderWidth: 0 },
  },
  series: [
    {
      name: "Impulse response (stem)",
      type: "column",
      data: samples,
      color: t.palette[0],
      enableMouseTracking: false,
    },
    {
      name: "Impulse response",
      type: "scatter",
      data: samples.map((s, i) => (i === peakIndex ? { ...s, dataLabels: peakLabel } : s)),
      color: t.palette[0],
      marker: { radius: 8, symbol: "circle", lineColor: t.pageBg, lineWidth: 1 },
    },
  ],
});
