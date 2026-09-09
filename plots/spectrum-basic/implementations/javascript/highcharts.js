// anyplot.ai
// spectrum-basic: Frequency Spectrum Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated FFT magnitude spectrum of a sustained musical note (A4 = 440 Hz)
// with decaying harmonics riding on a noisy broadband noise floor.
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const fundamentalHz = 440;
const harmonics = [
  { freq: fundamentalHz * 1, peakDb: -5 },
  { freq: fundamentalHz * 2, peakDb: -15 },
  { freq: fundamentalHz * 3, peakDb: -22 },
  { freq: fundamentalHz * 4, peakDb: -28 },
  { freq: fundamentalHz * 5, peakDb: -33 },
];
const noiseFloorDb = -70;
const peakWidthOctaves = 0.04;

const nPoints = 300;
const freqMin = 20;
const freqMax = 20000;
const spectrum = Array.from({ length: nPoints }, (_, i) => {
  const frequency = freqMin * Math.pow(freqMax / freqMin, i / (nPoints - 1));
  let amplitudeDb = noiseFloorDb + (nextRandom() - 0.5) * 3;
  for (const h of harmonics) {
    const octaveDist = Math.log2(frequency / h.freq);
    const bumpDb = h.peakDb - noiseFloorDb;
    amplitudeDb +=
      bumpDb *
      Math.exp(-(octaveDist * octaveDist) / (2 * peakWidthOctaves * peakWidthOctaves));
  }
  return [frequency, amplitudeDb];
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "spectrum-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "logarithmic",
    min: freqMin,
    max: freqMax,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
    },
    title: { text: "Frequency (Hz)", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: -75,
    max: 0,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Amplitude (dB)", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
    area: {
      threshold: -75,
      fillOpacity: 0.15,
      lineWidth: 2.5,
    },
  },
  series: [{ name: "Amplitude", data: spectrum }],
});
