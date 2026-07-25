// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 85/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data: damped discrete-time impulse response (signal processing) -------
const sampleCount = 40;
const samples = [];
for (let n = 0; n < sampleCount; n += 1) {
  const amplitude = Math.exp(-n / 14) * Math.cos(n * 0.45);
  samples.push({ x: n, y: Math.round(amplitude * 1000) / 1000 });
}

// --- Chart -------------------------------------------------------------
// Highcharts has no lollipop/stem series in the core bundle, so the stem is
// built from two aligned series: a thin column (baseline-to-value stem) and
// a scatter series (the marker) — a standard core-only combo technique.
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
    min: -1,
    max: sampleCount,
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
    series: { animation: false },
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
      data: samples,
      color: t.palette[0],
      marker: { radius: 6, symbol: "circle", lineColor: t.pageBg, lineWidth: 1 },
    },
  ],
});
