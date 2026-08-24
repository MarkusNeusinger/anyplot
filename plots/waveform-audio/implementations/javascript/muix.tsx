// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-24
//# anyplot-orientation: landscape
// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated spoken utterance: a fundamental tone plus two harmonics, shaped by
// a handful of overlapping syllable envelopes and a touch of breath noise.
let lcgState = 42;
const nextRandom = () => {
  lcgState = (lcgState * 1103515245 + 12345) % 2147483648;
  return lcgState / 2147483648;
};

const sampleRateHz = 22050;
const durationSeconds = 2.0;
const sampleCount = Math.round(sampleRateHz * durationSeconds);
const fundamentalHz = 180;
const syllableCenters = [0.22, 0.5, 0.86, 1.18, 1.5, 1.78];
const syllableWidth = 0.13;

const envelopeAt = (time) =>
  syllableCenters.reduce((sum, center) => {
    const offset = (time - center) / syllableWidth;
    return sum + Math.exp(-0.5 * offset * offset);
  }, 0);

let peakEnvelope = 0;
for (let i = 0; i < sampleCount; i += 1) {
  peakEnvelope = Math.max(peakEnvelope, envelopeAt(i / sampleRateHz));
}

const rawSamples = new Float64Array(sampleCount);
for (let i = 0; i < sampleCount; i += 1) {
  const time = i / sampleRateHz;
  const envelope = envelopeAt(time) / peakEnvelope;
  const tone =
    Math.sin(2 * Math.PI * fundamentalHz * time) +
    0.5 * Math.sin(2 * Math.PI * fundamentalHz * 2 * time) +
    0.25 * Math.sin(2 * Math.PI * fundamentalHz * 3 * time);
  const breath = (nextRandom() - 0.5) * 0.07 * envelope;
  rawSamples[i] = envelope * (tone / 1.75) + breath;
}

// Min/max envelope downsampling — the standard DAW technique for rendering
// tens of thousands of samples without aliasing at a fixed pixel width.
const bucketCount = 900;
const bucketSize = Math.ceil(sampleCount / bucketCount);
const bucketTimes = [];
const upperEnvelope = [];
const lowerEnvelope = [];
for (let start = 0; start < sampleCount; start += bucketSize) {
  const end = Math.min(start + bucketSize, sampleCount);
  let bucketMax = -1;
  let bucketMin = 1;
  for (let i = start; i < end; i += 1) {
    const value = rawSamples[i];
    if (value > bucketMax) bucketMax = value;
    if (value < bucketMin) bucketMin = value;
  }
  bucketTimes.push((start + end) / 2 / sampleRateHz);
  upperEnvelope.push(bucketMax);
  lowerEnvelope.push(bucketMin);
}

const title = "Speech Utterance · waveform-audio · javascript · muix · anyplot.ai";
const titleHeight = 64;

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          fontFamily: "Roboto, Helvetica, Arial, sans-serif",
        }}
      >
        {title}
      </div>
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height - titleHeight}
        skipAnimation
        margin={{ top: 20, right: 40, bottom: 60, left: 80 }}
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: bucketTimes,
            scaleType: "linear",
            label: "Time (s)",
            valueFormatter: (value) => `${value.toFixed(2)}s`,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            min: -1,
            max: 1,
            label: "Amplitude",
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        series={[
          {
            id: "upper-envelope",
            data: upperEnvelope,
            area: true,
            showMark: false,
            curve: "linear",
            color: t.palette[0],
            label: "Amplitude",
          },
          {
            id: "lower-envelope",
            data: lowerEnvelope,
            area: true,
            showMark: false,
            curve: "linear",
            color: t.palette[0],
          },
        ]}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiAreaElement-root": { fillOpacity: 0.55 },
          "& .MuiLineElement-root": { strokeWidth: 1.25 },
          "& .MuiChartsGrid-horizontalLine": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine
          y={0}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5, opacity: 0.6 }}
        />
      </LineChart>
    </div>
  );
}
