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
const WINDOW = 256; // STFT frame length in samples (Hann window)
const HOP = 64; // samples between frame starts: 75 % overlap
const DYNAMIC_RANGE_DB = 60; // colour scale spans the loudest cell down to this many dB below it
const COLORBAR_TICK_TARGET = 6;
const POWER_LABEL = "Power (dB re full scale)";
const FREQUENCY_LABEL = "Frequency (Hz)";

// Columns: set these to your data's column names
const TIME = "Time (s)"; // role: extra
const AMPLITUDE = "Amplitude"; // role: signal

// Data: replace this block with your own records, one object per row
// A 2.5 s linear chirp from 150 Hz to 1600 Hz sampled at 4 kHz, over a faint noise floor
const data = (() => {
  const sampleRate = 4000;
  const duration = 2.5;
  const fStart = 150;
  const fEnd = 1600;
  let s = 42 >>> 0;
  const rand = () => {
    s = (((s * 1664525) >>> 0) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
  return Array.from({ length: sampleRate * duration }, (_, n) => {
    const time = n / sampleRate;
    const phase = 2 * Math.PI * (fStart * time + ((fEnd - fStart) / (2 * duration)) * time * time);
    return { [TIME]: time, [AMPLITUDE]: Math.sin(phase) + (rand() - 0.5) * 0.08 };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[TIME] - b[TIME]);
const signal = rows.map((d) => d[AMPLITUDE]);
const tStart = rows[0][TIME];
const sampleRate = (rows.length - 1) / (rows[rows.length - 1][TIME] - tStart);
const nyquist = sampleRate / 2;
const freqStep = sampleRate / WINDOW;
const frameStep = HOP / sampleRate;

// Short-time Fourier transform: Hann-windowed frames, one-sided magnitude in dB
const hann = Array.from({ length: WINDOW }, (_, n) => 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (WINDOW - 1)));
const cosTable = Array.from({ length: WINDOW }, (_, i) => Math.cos((2 * Math.PI * i) / WINDOW));
const sinTable = Array.from({ length: WINDOW }, (_, i) => Math.sin((2 * Math.PI * i) / WINDOW));
const frameCount = Math.floor((signal.length - WINDOW) / HOP) + 1;
const power = Array.from({ length: frameCount }, (_, f) => {
  const frame = hann.map((w, n) => w * signal[f * HOP + n]);
  return Array.from({ length: WINDOW / 2 + 1 }, (_, k) => {
    let re = 0;
    let im = 0;
    for (let n = 0; n < WINDOW; n += 1) {
      const idx = (k * n) % WINDOW;
      re += frame[n] * cosTable[idx];
      im -= frame[n] * sinTable[idx];
    }
    return 20 * Math.log10((2 / WINDOW) * Math.hypot(re, im) + 1e-9);
  });
});
const maxDb = Math.max(...power.map((col) => Math.max(...col)));
const minDb = maxDb - DYNAMIC_RANGE_DB;

// Each cell is centred on its frame's centre time and its bin's frequency
const seqRgb = t.seq.map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
const cells = power.flatMap((col, f) =>
  col.map((db, k) => {
    const v = Math.min(1, Math.max(0, (db - minDb) / DYNAMIC_RANGE_DB));
    const centre = tStart + (f * HOP + WINDOW / 2) / sampleRate;
    return {
      key: `${f}-${k}`,
      t0: centre - frameStep / 2,
      t1: centre + frameStep / 2,
      f0: Math.max(0, (k - 0.5) * freqStep),
      f1: Math.min(nyquist, (k + 0.5) * freqStep),
      fill: `rgb(${seqRgb[0].map((c, j) => Math.round(c + (seqRgb[1][j] - c) * v)).join(",")})`,
    };
  }),
);
const xMin = cells[0].t0;
const xMax = cells[cells.length - 1].t1;

const rawStep = DYNAMIC_RANGE_DB / COLORBAR_TICK_TARGET;
const stepMagnitude = 10 ** Math.floor(Math.log10(rawStep));
const dbStep = [1, 2, 5, 10].map((m) => m * stepMagnitude).find((s) => s >= rawStep);
const dbTicks = Array.from(
  { length: Math.floor(maxDb / dbStep) - Math.ceil(minDb / dbStep) + 1 },
  (_, i) => (Math.ceil(minDb / dbStep) + i) * dbStep,
);

const TITLE = "spectrogram-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} samples at ${Math.round(sampleRate).toLocaleString(
  "en-US",
)} Hz · Hann window ${WINDOW} samples (${((WINDOW / sampleRate) * 1000).toFixed(0)} ms), hop ${HOP} · ${freqStep.toFixed(
  1,
)} Hz bins`;
const HEADER_H = 80;
const BAR_W = 22;
const BAR_GAP = 24;

function SpectrogramCells() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g shapeRendering="crispEdges">
      {cells.map((c) => (
        <rect
          key={c.key}
          x={xScale(c.t0)}
          y={yScale(c.f1)}
          width={xScale(c.t1) - xScale(c.t0) + 0.6}
          height={yScale(c.f0) - yScale(c.f1) + 0.6}
          fill={c.fill}
        />
      ))}
    </g>
  );
}

function Colorbar() {
  const { left, top, width, height } = useDrawingArea();
  const x = left + width + BAR_GAP;
  const yOf = (db) => top + ((maxDb - db) / DYNAMIC_RANGE_DB) * height;
  return (
    <g>
      <defs>
        <linearGradient id="spectrogramColorbar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={x} y={top} width={BAR_W} height={height} fill="url(#spectrogramColorbar)" />
      {dbTicks.map((db) => (
        <g key={db}>
          <line x1={x + BAR_W} x2={x + BAR_W + 6} y1={yOf(db)} y2={yOf(db)} stroke={t.inkSoft} />
          <text x={x + BAR_W + 10} y={yOf(db)} dominantBaseline="middle" fontSize={14} fill={t.inkSoft}>
            {db.toFixed(0)}
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
            min: 0,
            max: nyquist,
            label: FREQUENCY_LABEL,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <SpectrogramCells />
        <Colorbar />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
