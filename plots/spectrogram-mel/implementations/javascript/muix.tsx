// anyplot.ai
// spectrogram-mel: Mel-Spectrogram for Audio Analysis
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const N_MELS = 64; // number of mel filter banks
const N_FFT = 1024; // STFT frame length in samples (Hann window)
const HOP = 400; // samples between frame starts
const DYNAMIC_RANGE_DB = 70; // colour scale spans the peak down to this many dB below it; quieter cells clamp to the low end
const TICK_EVERY_BANDS = 8; // frequency ticks at every eighth mel band edge
const COLORBAR_TICK_TARGET = 8;
const POWER_LABEL = "Power (dB re peak)";
const FREQUENCY_LABEL = "Frequency (Hz, mel-scaled)";

// Columns: set these to your data's column names
const TIME = "Time (s)"; // role: extra
const AMPLITUDE = "Amplitude"; // role: audio_signal

// Data: replace this block with your own records, one object per row
// A sung C-major arpeggio (C4, E4, G4, C5) with three decaying harmonics, 5 Hz vibrato
// and a breathy onset, sampled at 16 kHz for 2.4 s
const data = (() => {
  const sampleRate = 16000;
  const duration = 2.4;
  const notes = [261.63, 329.63, 392.0, 523.25];
  const harmonicAmps = [1, 0.5, 0.22];
  const noteDuration = duration / notes.length;
  let s = 42 >>> 0;
  const rand = () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
  return Array.from({ length: Math.round(sampleRate * duration) }, (_, i) => {
    const time = i / sampleRate;
    const noteIndex = Math.min(notes.length - 1, Math.floor(time / noteDuration));
    const localT = time - noteIndex * noteDuration;
    const envelope = Math.sin(Math.PI * Math.min(1, localT / noteDuration));
    // Vibrato as a frequency modulation of ±0.6 % at 5 Hz, integrated into the phase
    const warpedTime = time + (0.006 * (1 - Math.cos(2 * Math.PI * 5 * time))) / (2 * Math.PI * 5);
    const tone = harmonicAmps.reduce(
      (acc, amp, h) => acc + amp * Math.sin(2 * Math.PI * notes[noteIndex] * (h + 1) * warpedTime),
      0,
    );
    const breathyOnset = Math.exp(-time / 0.03) * 0.16 * (2 * rand() - 1);
    const noiseFloor = 0.006 * (2 * rand() - 1);
    return { [TIME]: time, [AMPLITUDE]: 0.6 * envelope * tone + breathyOnset + noiseFloor };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[TIME] - b[TIME]);
const signal = rows.map((d) => d[AMPLITUDE]);
const tStart = rows[0][TIME];
const sampleRate = (rows.length - 1) / (rows[rows.length - 1][TIME] - tStart);
const nFreq = N_FFT / 2 + 1;
const frameCount = Math.floor((signal.length - N_FFT) / HOP) + 1;

// Mel filterbank (HTK mel formula) with Slaney area normalisation, so the wider
// high-frequency filters do not sum more broadband noise than the narrow low ones
const melMax = 2595 * Math.log10(1 + sampleRate / 2 / 700);
const melStep = melMax / (N_MELS + 1);
const hzEdges = Array.from({ length: N_MELS + 2 }, (_, i) => 700 * (10 ** ((i * melStep) / 2595) - 1));
const binEdges = hzEdges.map((hz) => Math.floor(((N_FFT + 1) * hz) / sampleRate));
const melFilters = Array.from({ length: N_MELS }, (_, i) => {
  const [lo, mid, hi] = [binEdges[i], binEdges[i + 1], binEdges[i + 2]];
  const norm = 2 / (hzEdges[i + 2] - hzEdges[i]);
  return Array.from({ length: nFreq }, (_, k) =>
    k >= lo && k < mid
      ? ((k - lo) / Math.max(1, mid - lo)) * norm
      : k >= mid && k < hi
        ? ((hi - k) / Math.max(1, hi - mid)) * norm
        : 0,
  );
});

// STFT power per frame, then mel power, then dB relative to the peak
const hann = Array.from({ length: N_FFT }, (_, n) => 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (N_FFT - 1)));
const cosTable = Array.from({ length: N_FFT }, (_, i) => Math.cos((2 * Math.PI * i) / N_FFT));
const sinTable = Array.from({ length: N_FFT }, (_, i) => Math.sin((2 * Math.PI * i) / N_FFT));
const melPower = Array.from({ length: frameCount }, (_, f) => {
  const frame = hann.map((w, n) => w * signal[f * HOP + n]);
  const spectrum = Array.from({ length: nFreq }, (_, k) => {
    let re = 0;
    let im = 0;
    for (let n = 0; n < N_FFT; n += 1) {
      const idx = (k * n) % N_FFT;
      re += frame[n] * cosTable[idx];
      im -= frame[n] * sinTable[idx];
    }
    return (re * re + im * im) / N_FFT;
  });
  return melFilters.map((filter) => filter.reduce((acc, w, k) => acc + w * spectrum[k], 0));
});
const peakPower = Math.max(...melPower.map((col) => Math.max(...col)));

// Cells: one per frame and mel band, centred on the frame's centre time and the band's centre mel
const frameStep = HOP / sampleRate;
const seqRgb = t.seq.map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
const cells = melPower.flatMap((col, f) =>
  col.map((p, m) => {
    const db = Math.max(-DYNAMIC_RANGE_DB, 10 * Math.log10(Math.max(p, 1e-12) / peakPower));
    const v = (db + DYNAMIC_RANGE_DB) / DYNAMIC_RANGE_DB;
    const centre = tStart + (f * HOP + N_FFT / 2) / sampleRate;
    return {
      key: `${f}-${m}`,
      t0: centre - frameStep / 2,
      t1: centre + frameStep / 2,
      mel0: (m + 0.5) * melStep,
      mel1: (m + 1.5) * melStep,
      fill: `rgb(${seqRgb[0].map((c, j) => Math.round(c + (seqRgb[1][j] - c) * v)).join(",")})`,
    };
  }),
);
const xMin = cells[0].t0;
const xMax = cells[cells.length - 1].t1;
const yMin = 0.5 * melStep;
const yMax = (N_MELS + 0.5) * melStep;
const melTicks = Array.from(
  { length: Math.floor(N_MELS / TICK_EVERY_BANDS) + 1 },
  (_, i) => (i * TICK_EVERY_BANDS + 0.5) * melStep,
);

const rawStep = DYNAMIC_RANGE_DB / COLORBAR_TICK_TARGET;
const stepMagnitude = 10 ** Math.floor(Math.log10(rawStep));
const dbStep = [1, 2, 5, 10].map((mul) => mul * stepMagnitude).find((s) => s >= rawStep);
const dbTicks = Array.from({ length: Math.floor(DYNAMIC_RANGE_DB / dbStep) + 1 }, (_, i) => -i * dbStep);

const TITLE = "spectrogram-mel · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} samples at ${Math.round(sampleRate).toLocaleString(
  "en-US",
)} Hz · ${N_MELS} mel bands up to ${Math.round(sampleRate / 2).toLocaleString("en-US")} Hz · FFT ${N_FFT}, hop ${HOP} (${(
  frameStep * 1000
).toFixed(0)} ms per frame)`;
const HEADER_H = 80;
const BAR_W = 22;
const BAR_GAP = 24;

function MelCells() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g shapeRendering="crispEdges">
      {cells.map((c) => (
        <rect
          key={c.key}
          x={xScale(c.t0)}
          y={yScale(c.mel1)}
          width={xScale(c.t1) - xScale(c.t0) + 0.6}
          height={yScale(c.mel0) - yScale(c.mel1) + 0.6}
          fill={c.fill}
        />
      ))}
    </g>
  );
}

function Colorbar() {
  const { left, top, width, height } = useDrawingArea();
  const x = left + width + BAR_GAP;
  return (
    <g>
      <defs>
        <linearGradient id="melColorbar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={x} y={top} width={BAR_W} height={height} fill="url(#melColorbar)" />
      {dbTicks.map((db) => (
        <g key={db}>
          <line
            x1={x + BAR_W}
            x2={x + BAR_W + 6}
            y1={top + (-db / DYNAMIC_RANGE_DB) * height}
            y2={top + (-db / DYNAMIC_RANGE_DB) * height}
            stroke={t.inkSoft}
          />
          <text
            x={x + BAR_W + 10}
            y={top + (-db / DYNAMIC_RANGE_DB) * height}
            dominantBaseline="middle"
            fontSize={14}
            fill={t.inkSoft}
          >
            {db === 0 ? "0" : `−${-db}`}
          </text>
        </g>
      ))}
      <text
        x={x + BAR_W + 62}
        y={top + height / 2}
        textAnchor="middle"
        fontSize={16}
        fill={t.ink}
        transform={`rotate(90, ${x + BAR_W + 62}, ${top + height / 2})`}
      >
        {POWER_LABEL}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        margin={{ top: 12, right: 140, bottom: 12, left: 24 }}
        skipAnimation
        series={[]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: TIME,
            height: 62,
            tickNumber: 12,
            valueFormatter: (v) => v.toFixed(1),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            tickInterval: melTicks,
            valueFormatter: (mel) => Math.round(700 * (10 ** (mel / 2595) - 1)).toLocaleString("en-US"),
            label: FREQUENCY_LABEL,
            width: 92,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <MelCells />
        <Colorbar />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
