// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-24

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const N_FRAMES = 80;
const SEC_PER_FRAME = 0.05;
const TOTAL_SEC = N_FRAMES * SEC_PER_FRAME;

const CHORDS = [
  { label: "C major", pcs: [0, 4, 7],  start: 0,  end: 20 },
  { label: "G major", pcs: [7, 11, 2], start: 20, end: 40 },
  { label: "A minor", pcs: [9, 0, 4],  start: 40, end: 60 },
  { label: "F major", pcs: [5, 9, 0],  start: 60, end: 80 },
];

// Deterministic LCG seeded at 42
function makeLCG(seed) {
  let s = seed >>> 0;
  return () => { s = (((s * 1664525) >>> 0) + 1013904223) >>> 0; return s / 0x100000000; };
}
const rand = makeLCG(42);

// 12 × 80 chroma matrix; chord tones high energy, overtones medium, rest noise
const chroma = Array.from({ length: 12 }, (_, pc) =>
  Array.from({ length: N_FRAMES }, (_, f) => {
    const chord = CHORDS.find(c => f >= c.start && f < c.end);
    const active   = chord ? chord.pcs.includes(pc) : false;
    const overtone = chord ? chord.pcs.map(p => (p + 7) % 12).includes(pc) : false;
    const base = active   ? 0.65 + rand() * 0.30
               : overtone ? 0.22 + rand() * 0.18
               :             rand() * 0.16;
    return Math.min(1.0, base);
  })
);

// Imprint sequential colormap: seq[0]=#009E73 → seq[1]=#4467A3
function hexRgb(h) {
  return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
}
function seqColor(v) {
  const [r1, g1, b1] = hexRgb(t.seq[0]);
  const [r2, g2, b2] = hexRgb(t.seq[1]);
  return `rgb(${Math.round(r1 + (r2 - r1) * v)},${Math.round(g1 + (g2 - g1) * v)},${Math.round(b1 + (b2 - b1) * v)})`;
}

// Heatmap cells, chord dividers, and chord labels — drawn using MUI X scale hooks
function HeatmapCells() {
  const { top, height: gH } = useDrawingArea();
  const xScale = useXScale();
  // Use exact gH/12 step to fill rows without gaps regardless of band scale padding
  const step = gH / 12;
  const divColor = window.ANYPLOT_THEME === "dark"
    ? "rgba(240,239,232,0.4)"
    : "rgba(26,26,23,0.4)";

  return (
    <>
      {chroma.flatMap((row, pc) =>
        row.map((val, f) => (
          <rect
            key={`${pc}-${f}`}
            x={xScale(f * SEC_PER_FRAME)}
            y={top + (11 - pc) * step}
            width={xScale((f + 1) * SEC_PER_FRAME) - xScale(f * SEC_PER_FRAME) + 0.5}
            height={step + 0.5}
            fill={seqColor(val)}
          />
        ))
      )}
      {/* Chord-change dividers at 1s / 2s / 3s — semi-transparent in both themes */}
      {[1, 2, 3].map(sec => (
        <line
          key={sec}
          x1={xScale(sec)} y1={top}
          x2={xScale(sec)} y2={top + gH}
          stroke={divColor} strokeWidth={2.5}
        />
      ))}
      {CHORDS.map(c => (
        <text
          key={c.label}
          x={xScale((c.start + (c.end - c.start) / 2) * SEC_PER_FRAME)}
          y={top - 10}
          textAnchor="middle" fontSize={13} fill={t.inkSoft}
          fontFamily="Inter, system-ui, sans-serif"
        >
          {c.label}
        </text>
      ))}
    </>
  );
}

// Colorbar gradient using drawing-area position from MUI X context
function Colorbar() {
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const cbX = left + gW + 22;
  const cbW = 20;

  return (
    <>
      <defs>
        <linearGradient id="cbGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={cbX} y={top} width={cbW} height={gH} fill="url(#cbGrad)" />
      <text x={cbX + cbW / 2} y={top - 6} textAnchor="middle" fontSize={13} fill={t.inkSoft} fontFamily="Inter, system-ui, sans-serif">1.0</text>
      <text x={cbX + cbW / 2} y={top + gH + 16} textAnchor="middle" fontSize={13} fill={t.inkSoft} fontFamily="Inter, system-ui, sans-serif">0.0</text>
      <text
        x={cbX + cbW + 16} y={top + gH / 2}
        textAnchor="middle" fontSize={14} fill={t.inkSoft}
        fontFamily="Inter, system-ui, sans-serif"
        transform={`rotate(90, ${cbX + cbW + 16}, ${top + gH / 2})`}
      >
        Energy
      </text>
    </>
  );
}

function ChartTitle() {
  const { top } = useDrawingArea();
  return (
    <text
      x={width / 2} y={top - 46}
      textAnchor="middle" fontSize={22} fontWeight={500}
      fill={t.ink} fontFamily="Inter, system-ui, sans-serif"
    >
      heatmap-chromagram · javascript · muix · anyplot.ai
    </text>
  );
}

export default function Chart() {
  return (
    <ChartContainer
      width={width}
      height={height}
      series={[]}
      xAxis={[{
        scaleType: "linear",
        min: 0,
        max: TOTAL_SEC,
        label: "Time (seconds)",
        valueFormatter: (v) => `${v.toFixed(1)}s`,
      }]}
      yAxis={[{
        scaleType: "band",
        data: [...PITCH_CLASSES].reverse(),
        label: "Pitch Class",
      }]}
      margin={{ left: 70, right: 90, top: 80, bottom: 70 }}
    >
      <ChartTitle />
      <HeatmapCells />
      <Colorbar />
      <ChartsXAxis />
      <ChartsYAxis />
    </ChartContainer>
  );
}
