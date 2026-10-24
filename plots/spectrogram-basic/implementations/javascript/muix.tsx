// anyplot.ai
// spectrogram-basic: Spectrogram Time-Frequency Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-09

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const WINDOW = 256;
const HOP = 64;
const FREQ_BINS = WINDOW / 2;
const DYNAMIC_RANGE_DB = 60;

// Columns: set these to your data's column names
const SIGNAL = "Signal Amplitude"; // role: signal
const SAMPLE_RATE = 4000; // role: sample_rate

// Data: replace this block with your own records
const durationSec = 2.5;
const nSamples = SAMPLE_RATE * durationSec;
const fStart = 150;
const fEnd = 1600;
let lcgSeed = 42;
const data: Array<Record<string, number>> = [];
for (let n = 0; n < nSamples; n++) {
  lcgSeed = (((lcgSeed * 1664525) >>> 0) + 1013904223) >>> 0;
  const u = lcgSeed / 0x100000000;
  const time = n / SAMPLE_RATE;
  const phase =
    2 * Math.PI * (fStart * time + ((fEnd - fStart) / (2 * durationSec)) * time * time);
  data.push({
    [SIGNAL]: Math.sin(phase) + (u - 0.5) * 0.08,
  });
}

// Plot: reads only data and the constants above
const signal = data.map((row) => Number(row[SIGNAL]));
const totalSamples = signal.length;
const timeStep = HOP / SAMPLE_RATE;
const freqStep = SAMPLE_RATE / WINDOW;
const nFrames = Math.floor((totalSamples - WINDOW) / HOP) + 1;

const hann = Array.from(
  { length: WINDOW },
  (_, n) => 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (WINDOW - 1)),
);

const power: Float64Array[] = [];
let maxDb = -Infinity;
for (let f = 0; f < nFrames; f++) {
  const start = f * HOP;
  const re = new Float64Array(WINDOW);
  const im = new Float64Array(WINDOW);
  for (let n = 0; n < WINDOW; n++) {
    re[n] = signal[start + n] * hann[n];
  }
  // Iterative radix-2 Cooley-Tukey FFT
  for (let i = 1, j = 0; i < WINDOW; i++) {
    let bit = WINDOW >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      const tr = re[i];
      re[i] = re[j];
      re[j] = tr;
      const ti = im[i];
      im[i] = im[j];
      im[j] = ti;
    }
  }
  for (let len = 2; len <= WINDOW; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang);
    const wi = Math.sin(ang);
    for (let i = 0; i < WINDOW; i += len) {
      let curWr = 1;
      let curWi = 0;
      for (let j = 0; j < len / 2; j++) {
        const ur = re[i + j];
        const ui = im[i + j];
        const vr = re[i + j + len / 2] * curWr - im[i + j + len / 2] * curWi;
        const vi = re[i + j + len / 2] * curWi + im[i + j + len / 2] * curWr;
        re[i + j] = ur + vr;
        im[i + j] = ui + vi;
        re[i + j + len / 2] = ur - vr;
        im[i + j + len / 2] = ui - vi;
        const nextWr = curWr * wr - curWi * wi;
        curWi = curWr * wi + curWi * wr;
        curWr = nextWr;
      }
    }
  }
  const row = new Float64Array(FREQ_BINS);
  for (let k = 0; k < FREQ_BINS; k++) {
    const mag = (2 / WINDOW) * Math.sqrt(re[k] * re[k] + im[k] * im[k]);
    const db = 20 * Math.log10(mag + 1e-9);
    row[k] = db;
    if (db > maxDb) maxDb = db;
  }
  power.push(row);
}

const minDb = maxDb - DYNAMIC_RANGE_DB;
const totalSec = ((nFrames - 1) * HOP + WINDOW) / SAMPLE_RATE;

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

function SpectrogramLayer() {
  const { width } = window.ANYPLOT_SIZE;
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const cbX = left + gW + 24;
  const cbW = 20;

  return (
    <g>
      <text
        x={width / 2}
        y={top - 36}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        Linear Chirp Spectrogram · spectrogram-basic · javascript · muix · anyplot.ai
      </text>
      {power.flatMap((row, f) =>
        Array.from(row).map((db, k) => {
          const norm = Math.min(1, Math.max(0, (db - minDb) / (maxDb - minDb)));
          const x0 = xScale(f * timeStep);
          const x1 = xScale((f + 1) * timeStep);
          const yTop = yScale((k + 1) * freqStep);
          const yBottom = yScale(k * freqStep);
          const r = Math.round(seqR1 + (seqR2 - seqR1) * norm);
          const g = Math.round(seqG1 + (seqG2 - seqG1) * norm);
          const b = Math.round(seqB1 + (seqB2 - seqB1) * norm);
          return (
            <rect
              key={`${f}-${k}`}
              x={x0}
              y={yTop}
              width={x1 - x0 + 0.5}
              height={yBottom - yTop + 0.5}
              fill={`rgb(${r},${g},${b})`}
            />
          );
        }),
      )}
      <defs>
        <linearGradient id="cbGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={cbX} y={top} width={cbW} height={gH} fill="url(#cbGrad)" rx={2} />
      <text
        x={cbX + cbW / 2}
        y={top - 8}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        {Math.round(maxDb)} dB
      </text>
      <text
        x={cbX + cbW / 2}
        y={top + gH + 18}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        {Math.round(minDb)} dB
      </text>
      <text
        x={cbX + cbW + 20}
        y={top + gH / 2}
        textAnchor="middle"
        fontSize={15}
        fill={t.ink}
        transform={`rotate(90, ${cbX + cbW + 20}, ${top + gH / 2})`}
      >
        Power (dB)
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        series={[]}
        xAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: totalSec,
            height: 60,
            label: "Time (s)",
            valueFormatter: (v: number) => `${v.toFixed(1)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: FREQ_BINS * freqStep,
            width: 96,
            label: "Frequency (Hz)",
            valueFormatter: (v: number) => `${Math.round(v)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ left: 108, right: 98, top: 80, bottom: 72 }}
      >
        <SpectrogramLayer />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
