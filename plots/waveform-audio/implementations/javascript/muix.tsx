// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const FULL_SCALE = 1; // normalized amplitude spans -1 to +1
// Min/max envelope buckets across the plot width: few enough that each bucket
// spans a full cycle of the tone, so its maximum is a true peak, and the
// outline follows the peaks instead of zigzagging between cycle phases.
const BUCKETS = 300;
const TITLE = "waveform-audio · javascript · muix · anyplot.ai";
const TITLE_H = 80;

// Columns: set these to your data's column names
const TIME = "Time (s)"; // role: time
const AMPLITUDE = "Amplitude (normalized)"; // role: amplitude

// Data: replace this block with your own records, one object per row
// A simulated spoken utterance, 2 s at 22.05 kHz: a 180 Hz fundamental with
// two harmonics, shaped by six overlapping syllable envelopes plus a little
// breath noise.
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  const rate = 22050;
  const count = Math.round(rate * 2.0);
  const f0 = 180;
  const syllables = [0.22, 0.5, 0.86, 1.18, 1.5, 1.78];
  const envelopeAt = (time) => syllables.reduce((sum, c) => sum + Math.exp(-0.5 * ((time - c) / 0.13) ** 2), 0);
  let peak = 0;
  for (let i = 0; i < count; i += 1) peak = Math.max(peak, envelopeAt(i / rate));
  return Array.from({ length: count }, (_, i) => {
    const time = i / rate;
    const envelope = envelopeAt(time) / peak;
    const tone =
      Math.sin(2 * Math.PI * f0 * time) +
      0.5 * Math.sin(2 * Math.PI * f0 * 2 * time) +
      0.25 * Math.sin(2 * Math.PI * f0 * 3 * time);
    const breath = (rand() - 0.5) * 0.07 * envelope;
    return { [TIME]: Math.round(time * 1e6) / 1e6, [AMPLITUDE]: Math.round((envelope * (tone / 1.75) + breath) * 1e4) / 1e4 };
  });
})();

// Plot: reads only data and the constants above
const samples = data
  .filter((d) => d[TIME] != null && d[AMPLITUDE] != null)
  .sort((a, b) => a[TIME] - b[TIME]);

// Min/max envelope: each bucket keeps the highest and lowest sample it holds,
// so every peak survives the reduction to the plot width without aliasing.
const bucketSize = Math.ceil(samples.length / BUCKETS);
const bucketTimes = [];
const upper = [];
const lower = [];
for (let start = 0; start < samples.length; start += bucketSize) {
  const bucket = samples.slice(start, start + bucketSize).map((d) => d[AMPLITUDE]);
  bucketTimes.push((samples[start][TIME] + samples[start + bucket.length - 1][TIME]) / 2);
  upper.push(Math.max(...bucket));
  lower.push(Math.min(...bucket));
}

// Focal point: the bucket with the largest absolute excursion
const peakIndex = upper.reduce((best, v, i) => (Math.max(v, -lower[i]) > Math.max(upper[best], -lower[best]) ? i : best), 0);
const peakValue = Math.max(upper[peakIndex], -lower[peakIndex]);
const peakSigned = upper[peakIndex] === peakValue ? upper[peakIndex] : lower[peakIndex];
const tStart = samples[0][TIME];
const tEnd = samples[samples.length - 1][TIME];
const duration = tEnd - tStart;
const TIME_UNIT = TIME.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const SUBTITLE = `${samples.length.toLocaleString("en-US")} samples over ${duration.toFixed(2)} ${TIME_UNIT} · drawn as a min/max envelope of ${upper.length} buckets`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        margin={{ top: 28, right: 48, bottom: 12, left: 24 }}
        grid={{ horizontal: true, vertical: true }}
        xAxis={[
          {
            data: bucketTimes,
            scaleType: "linear",
            min: tStart,
            max: tEnd,
            label: TIME,
            valueFormatter: (v) => v.toFixed(2),
            tickNumber: 10,
            height: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: -FULL_SCALE,
            max: FULL_SCALE,
            label: AMPLITUDE,
            valueFormatter: (v) => v.toFixed(1),
            width: 80,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        series={[
          {
            id: "upper",
            data: upper,
            area: true,
            showMark: ({ index }) => index === peakIndex && upper[index] === peakValue,
            shape: "circle",
            curve: "linear",
            color: t.palette[0],
            label: AMPLITUDE,
          },
          {
            id: "lower",
            data: lower,
            area: true,
            showMark: ({ index }) => index === peakIndex && -lower[index] === peakValue,
            shape: "circle",
            curve: "linear",
            color: t.palette[0],
          },
        ]}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.5 },
          "& .MuiLineChart-line": { strokeWidth: 1.25 },
          "& .MuiLineChart-mark": { fill: t.ink, stroke: t.pageBg, strokeWidth: 2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine y={0} lineStyle={{ stroke: t.ink, strokeWidth: 1.5, opacity: 0.75 }} />
        <ChartsReferenceLine
          x={bucketTimes[peakIndex]}
          label={`Largest excursion ${peakSigned.toFixed(2)}`}
          labelAlign={peakSigned < 0 ? "end" : "start"}
          spacing={{ x: 8, y: 6 }}
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.25, strokeDasharray: "5 5" }}
        />
      </LineChart>
    </div>
  );
}
