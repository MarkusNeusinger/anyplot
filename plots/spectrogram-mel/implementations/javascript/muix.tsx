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
const N_FFT = 1024;
const HOP = 400;
const N_FREQ = N_FFT / 2 + 1;
const DB_FLOOR = -80;
const COLOR_GAMMA = 0.6;

// Columns: set these to your data's column names
const AUDIO_SIGNAL = "Audio Waveform"; // role: audio_signal
const SAMPLE_RATE = 16000; // role: sample_rate
const N_MELS = 64; // role: n_mels

// Data: replace this block with your own records
const durationSec = 2.4;
const nSamples = Math.round(SAMPLE_RATE * durationSec);
const notes = [261.63, 329.63, 392.0, 523.25];
const noteDuration = durationSec / notes.length;
const harmonicAmps = [1, 0.5, 0.22];

let lcgSeed = 42;
const data: Array<Record<string, number>> = [];
for (let i = 0; i < nSamples; i++) {
  const time = i / SAMPLE_RATE;
  const noteIndex = Math.min(notes.length - 1, Math.floor(time / noteDuration));
  const localT = time - noteIndex * noteDuration;
  const envelope = Math.sin(Math.PI * Math.min(1, localT / noteDuration));
  const vibrato = 1 + 0.006 * Math.sin(2 * Math.PI * 5 * time);
  const fundamental = notes[noteIndex];

  let tone = 0;
  for (let h = 0; h < harmonicAmps.length; h++) {
    tone +=
      harmonicAmps[h] *
      Math.sin(2 * Math.PI * fundamental * (h + 1) * vibrato * time);
  }
  lcgSeed = (Math.imul(lcgSeed, 1664525) + 1013904223) >>> 0;
  const u1 = lcgSeed / 0x100000000;
  lcgSeed = (Math.imul(lcgSeed, 1664525) + 1013904223) >>> 0;
  const u2 = lcgSeed / 0x100000000;
  const breathyOnset = Math.exp(-time / 0.03) * 0.16 * (2 * u1 - 1);
  const noiseFloor = 0.006 * (2 * u2 - 1);
  data.push({
    [AUDIO_SIGNAL]: 0.6 * envelope * tone + breathyOnset + noiseFloor,
  });
}

// Plot: reads only data and the constants above
const audioSignal = data.map((row) => Number(row[AUDIO_SIGNAL]));
const totalSamples = audioSignal.length;
const nFrames = Math.floor((totalSamples - N_FFT) / HOP) + 1;

const hannWindow = new Float64Array(N_FFT);
for (let n = 0; n < N_FFT; n++) {
  hannWindow[n] = 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (N_FFT - 1));
}

const fMax = SAMPLE_RATE / 2;
const melMax = 2595 * Math.log10(1 + fMax / 700);
const melEdges = Array.from(
  { length: N_MELS + 2 },
  (_, i) => (i * melMax) / (N_MELS + 1),
);
const hzEdges = melEdges.map((mel) => 700 * (10 ** (mel / 2595) - 1));
const binEdges = hzEdges.map((hz) =>
  Math.floor(((N_FFT + 1) * hz) / SAMPLE_RATE),
);

const melFilters: Float64Array[] = Array.from(
  { length: N_MELS },
  () => new Float64Array(N_FREQ),
);
for (let m = 1; m <= N_MELS; m++) {
  const left = binEdges[m - 1];
  const center = binEdges[m];
  const right = binEdges[m + 1];
  const filt = melFilters[m - 1];
  const norm = 2 / (hzEdges[m + 1] - hzEdges[m - 1] || 1);
  for (let k = left; k < center && k < N_FREQ; k++) {
    if (k >= 0) filt[k] = ((k - left) / (center - left || 1)) * norm;
  }
  for (let k = center; k < right && k < N_FREQ; k++) {
    if (k >= 0) filt[k] = ((right - k) / (right - center || 1)) * norm;
  }
}

let peakPower = 1e-10;
const melPower: Float64Array[] = [];
for (let f = 0; f < nFrames; f++) {
  const start = f * HOP;
  const re = new Float64Array(N_FFT);
  const im = new Float64Array(N_FFT);
  for (let n = 0; n < N_FFT; n++) {
    re[n] = audioSignal[start + n] * hannWindow[n];
  }
  for (let i = 1, j = 0; i < N_FFT; i++) {
    let bit = N_FFT >> 1;
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
  for (let len = 2; len <= N_FFT; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang);
    const wi = Math.sin(ang);
    for (let i = 0; i < N_FFT; i += len) {
      let curWr = 1;
      let curWi = 0;
      for (let k = 0; k < len / 2; k++) {
        const ur = re[i + k];
        const ui = im[i + k];
        const vr = re[i + k + len / 2] * curWr - im[i + k + len / 2] * curWi;
        const vi = re[i + k + len / 2] * curWi + im[i + k + len / 2] * curWr;
        re[i + k] = ur + vr;
        im[i + k] = ui + vi;
        re[i + k + len / 2] = ur - vr;
        im[i + k + len / 2] = ui - vi;
        const nextWr = curWr * wr - curWi * wi;
        const nextWi = curWr * wi + curWi * wr;
        curWr = nextWr;
        curWi = nextWi;
      }
    }
  }

  const power = new Float64Array(N_FREQ);
  for (let k = 0; k < N_FREQ; k++) {
    power[k] = (re[k] * re[k] + im[k] * im[k]) / N_FFT;
  }

  const melRow = new Float64Array(N_MELS);
  for (let m = 0; m < N_MELS; m++) {
    let sum = 0;
    const filt = melFilters[m];
    for (let k = 0; k < N_FREQ; k++) sum += filt[k] * power[k];
    melRow[m] = sum;
    if (sum > peakPower) peakPower = sum;
  }
  melPower.push(melRow);
}

const melDb: number[][] = melPower.map((row) =>
  Array.from(row).map((v) =>
    Math.max(DB_FLOOR, 10 * Math.log10(Math.max(v, 1e-10) / peakPower)),
  ),
);

const timeMax = (nFrames * HOP) / SAMPLE_RATE;
const yTicks = Array.from({ length: 9 }, (_, i) =>
  Math.round((i * N_MELS) / 8),
);

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

function MelSpectrogramLayer() {
  const { width } = window.ANYPLOT_SIZE;
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const cbX = left + gW + 26;
  const cbW = 20;

  return (
    <g>
      <text
        x={width / 2}
        y={top - 40}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        Vocal Melody Mel-Spectrogram · spectrogram-mel · javascript · muix · anyplot.ai
      </text>
      {melDb.flatMap((row, f) => {
        const x0 = xScale((f * HOP) / SAMPLE_RATE);
        const x1 = xScale(((f + 1) * HOP) / SAMPLE_RATE);
        return row.map((db, m) => {
          const frac = (db - DB_FLOOR) / -DB_FLOOR;
          const gFrac = Math.pow(Math.max(0, frac), COLOR_GAMMA);
          const r = Math.round(seqR1 + (seqR2 - seqR1) * gFrac);
          const g = Math.round(seqG1 + (seqG2 - seqG1) * gFrac);
          const b = Math.round(seqB1 + (seqB2 - seqB1) * gFrac);
          const yTop = yScale(m + 1);
          const yBottom = yScale(m);
          return (
            <rect
              key={`${f}-${m}`}
              x={x0}
              y={yTop}
              width={x1 - x0 + 0.5}
              height={yBottom - yTop + 0.5}
              fill={`rgb(${r},${g},${b})`}
            />
          );
        });
      })}
      <defs>
        <linearGradient id="melCbGrad" x1="0" y1="1" x2="0" y2="0">
          {[0, 0.25, 0.5, 0.75, 1].map((stop) => {
            const gFrac = Math.pow(stop, COLOR_GAMMA);
            const r = Math.round(seqR1 + (seqR2 - seqR1) * gFrac);
            const g = Math.round(seqG1 + (seqG2 - seqG1) * gFrac);
            const b = Math.round(seqB1 + (seqB2 - seqB1) * gFrac);
            return (
              <stop
                key={stop}
                offset={`${stop * 100}%`}
                stopColor={`rgb(${r},${g},${b})`}
              />
            );
          })}
        </linearGradient>
      </defs>
      <rect x={cbX} y={top} width={cbW} height={gH} fill="url(#melCbGrad)" rx={2} />
      <text
        x={cbX + cbW / 2}
        y={top - 10}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        0 dB
      </text>
      <text
        x={cbX + cbW / 2}
        y={top + gH + 18}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        -80 dB
      </text>
      <text
        x={cbX + cbW + 22}
        y={top + gH / 2}
        textAnchor="middle"
        fontSize={15}
        fill={t.ink}
        transform={`rotate(90, ${cbX + cbW + 22}, ${top + gH / 2})`}
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
            max: timeMax,
            height: 60,
            label: "Time (s)",
            valueFormatter: (v: number) => `${v.toFixed(1)}s`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: N_MELS,
            width: 108,
            label: "Frequency (mel-scaled)",
            tickInterval: yTicks,
            valueFormatter: (v: number) => {
              const hz = 700 * (10 ** (((v * melMax) / N_MELS) / 2595) - 1);
              if (hz >= 1000) {
                return `${(hz / 1000).toFixed(1).replace(/\.0$/, "")}k Hz`;
              }
              return `${Math.round(hz)} Hz`;
            },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ left: 120, right: 120, top: 88, bottom: 72 }}
      >
        <MelSpectrogramLayer />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
