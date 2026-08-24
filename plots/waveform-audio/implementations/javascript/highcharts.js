// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated spoken utterance: syllable amplitude envelope * multi-harmonic
// voice carrier, with fixed-seed jitter for a natural, non-synthetic texture.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}

const sampleRate = 8000; // Hz
const durationSeconds = 1.5;
const sampleCount = Math.round(sampleRate * durationSeconds); // 12,000 samples

const f0 = 180; // fundamental (voice pitch), Hz
const syllables = [
  { start: 0.05, end: 0.35, peak: 0.85 },
  { start: 0.42, end: 0.68, peak: 0.65 },
  { start: 0.78, end: 1.02, peak: 0.95 },
  { start: 1.12, end: 1.42, peak: 0.55 },
];

function syllableEnvelope(time) {
  let envelope = 0;
  for (const syllable of syllables) {
    if (time >= syllable.start && time <= syllable.end) {
      const phase = (time - syllable.start) / (syllable.end - syllable.start);
      const shape = Math.sin(Math.PI * phase) ** 1.5; // smooth rise/fall
      envelope = Math.max(envelope, shape * syllable.peak);
    }
  }
  return envelope;
}

const rawAmplitude = new Float32Array(sampleCount);
for (let i = 0; i < sampleCount; i++) {
  const time = i / sampleRate;
  const envelope = syllableEnvelope(time);
  const carrier =
    Math.sin(2 * Math.PI * f0 * time) +
    0.5 * Math.sin(2 * Math.PI * f0 * 2 * time) +
    0.25 * Math.sin(2 * Math.PI * f0 * 3 * time);
  const jitter = (lcgRandom() - 0.5) * 0.08;
  rawAmplitude[i] = Math.max(-1, Math.min(1, envelope * (carrier / 1.75 + jitter)));
}

// --- Min/max envelope downsampling (avoids aliasing at this zoom level) ----
const bucketCount = 900;
const samplesPerBucket = sampleCount / bucketCount;
const envelopeData = [];
for (let bucket = 0; bucket < bucketCount; bucket++) {
  const startIdx = Math.floor(bucket * samplesPerBucket);
  const endIdx = Math.floor((bucket + 1) * samplesPerBucket);
  let bucketMin = Infinity;
  let bucketMax = -Infinity;
  for (let i = startIdx; i < endIdx; i++) {
    const value = rawAmplitude[i];
    if (value < bucketMin) bucketMin = value;
    if (value > bucketMax) bucketMax = value;
  }
  const bucketTime = startIdx / sampleRate;
  envelopeData.push([bucketTime, bucketMax], [bucketTime, bucketMin]);
}

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
    text: "waveform-audio · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Time (s)", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter() {
        return this.value.toFixed(1);
      },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    min: 0,
    max: durationSeconds,
  },
  yAxis: {
    title: { text: "Amplitude", style: { color: t.inkSoft, fontSize: "16px" } },
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    gridLineColor: t.grid,
    min: -1,
    max: 1,
    tickInterval: 0.5,
    plotLines: [{ value: 0, color: t.inkSoft, width: 1.5, zIndex: 3 }],
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    area: {
      threshold: 0,
      lineWidth: 1,
      fillOpacity: 0.55,
      marker: { enabled: false },
      states: { hover: { enabled: false } },
    },
  },
  series: [{ name: "Amplitude", data: envelopeData, color: t.palette[0] }],
});
