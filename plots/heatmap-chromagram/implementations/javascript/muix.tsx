// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: muix 9.2.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Constants
const TIME_COL = "time";
const PITCH_COL = "pitch_class";
const ENERGY_COL = "energy";
const CHORD_COL = "chord";

const TITLE = "heatmap-chromagram · javascript · muix · anyplot.ai";
const SUBTITLE_PREFIX = "Chroma energy distribution across 12 pitch classes";
const X_AXIS_LABEL = "Time (seconds)";
const Y_AXIS_LABEL = "Pitch Class";
const COLORBAR_LABEL = "Energy";
const FONT = "Inter, system-ui, sans-serif";

const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const N_FRAMES = 80;
const SEC_PER_FRAME = 0.05;

// Flat scalar chord-section definitions ("label|pc1,pc2,pc3|startFrame|endFrame")
const CHORD_SECTIONS = [
  "C major|0,4,7|0|20",
  "G major|7,11,2|20|40",
  "A minor|9,0,4|40|60",
  "F major|5,9,0|60|80",
];

const parsedChords = CHORD_SECTIONS.map((s) => {
  const [label, pcsStr, startStr, endStr] = s.split("|");
  const pcs = pcsStr.split(",").map(Number);
  const overtones = pcs.map((p) => (p + 7) % 12);
  return {
    label,
    pcs,
    overtones,
    start: Number(startStr),
    end: Number(endStr),
  };
});

// Data — 12 pitch classes × 80 time frames = 960 flat scalar records
let lcgState = 42 >>> 0;
const data: Record<string, string | number>[] = [];

for (let pc = 0; pc < PITCH_CLASSES.length; pc++) {
  const pitchName = PITCH_CLASSES[pc];
  for (let f = 0; f < N_FRAMES; f++) {
    lcgState = (((lcgState * 1664525) >>> 0) + 1013904223) >>> 0;
    const randVal = lcgState / 0x100000000;
    const chord = parsedChords.find((c) => f >= c.start && f < c.end)!;
    const isActive = chord.pcs.includes(pc);
    const isOvertone = chord.overtones.includes(pc);
    const rawEnergy = isActive
      ? 0.65 + randVal * 0.3
      : isOvertone
        ? 0.22 + randVal * 0.18
        : randVal * 0.16;
    const energy = Number(Math.min(1.0, rawEnergy).toFixed(4));
    const timeSec = Number((f * SEC_PER_FRAME).toFixed(3));
    data.push({
      [TIME_COL]: timeSec,
      [PITCH_COL]: pitchName,
      [ENERGY_COL]: energy,
      [CHORD_COL]: chord.label,
    });
  }
}

// Derive pitch classes, frame step, time extent, and chord intervals from data
const pitchOrder = Array.from(new Set(data.map((r) => String(r[PITCH_COL]))));
const pitchIndexMap = new Map<string, number>(pitchOrder.map((p, idx) => [p, idx]));
const uniqueTimes = Array.from(new Set(data.map((r) => Number(r[TIME_COL])))).sort((a, b) => a - b);
const frameStepSec = uniqueTimes.length > 1 ? uniqueTimes[1] - uniqueTimes[0] : SEC_PER_FRAME;
const minTimeSec = uniqueTimes[0] ?? 0;
const maxTimeSec = (uniqueTimes[uniqueTimes.length - 1] ?? 0) + frameStepSec;

// Derive contiguous chord spans from time-ordered frames
const timeToChord = new Map<number, string>();
for (const r of data) {
  const tVal = Number(r[TIME_COL]);
  if (!timeToChord.has(tVal)) {
    timeToChord.set(tVal, String(r[CHORD_COL]));
  }
}

type ChordSpan = { label: string; startSec: number; endSec: number };
const chordSpans: ChordSpan[] = [];
for (const tVal of uniqueTimes) {
  const lbl = timeToChord.get(tVal)!;
  const last = chordSpans[chordSpans.length - 1];
  if (!last || last.label !== lbl) {
    chordSpans.push({ label: lbl, startSec: tVal, endSec: tVal + frameStepSec });
  } else {
    last.endSec = tVal + frameStepSec;
  }
}
const chordDividers = chordSpans.slice(1).map((c) => c.startSec);

const seq0Int = parseInt(t.seq[0].slice(1), 16);
const seq1Int = parseInt(t.seq[1].slice(1), 16);
const r1 = (seq0Int >> 16) & 255;
const g1 = (seq0Int >> 8) & 255;
const b1 = seq0Int & 255;
const r2 = (seq1Int >> 16) & 255;
const g2 = (seq1Int >> 8) & 255;
const b2 = seq1Int & 255;

const cells = data.map((row, idx) => {
  const timeSec = Number(row[TIME_COL]);
  const pitch = String(row[PITCH_COL]);
  const pcIdx = pitchIndexMap.get(pitch) ?? 0;
  const val = Number(row[ENERGY_COL]);
  const r = Math.round(r1 + (r2 - r1) * val);
  const g = Math.round(g1 + (g2 - g1) * val);
  const b = Math.round(b1 + (b2 - b1) * val);
  return {
    key: `${pcIdx}-${idx}`,
    pcIdx,
    timeSec,
    nextTimeSec: timeSec + frameStepSec,
    fill: `rgb(${r},${g},${b})`,
  };
});

function ChromagramLayer() {
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const xScale = useXScale();
  if (!xScale) return null;

  const nRows = pitchOrder.length;
  const step = gH / nRows;
  const divColor =
    window.ANYPLOT_THEME === "dark" ? "rgba(240,239,232,0.45)" : "rgba(26,26,23,0.45)";
  const cbX = left + gW + 24;
  const cbW = 20;

  return (
    <g>
      <defs>
        <linearGradient id="cbGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>

      {cells.map((cell) => {
        const x0 = Number(xScale(cell.timeSec) ?? 0);
        const x1 = Number(xScale(cell.nextTimeSec) ?? 0);
        return (
          <rect
            key={cell.key}
            x={x0}
            y={top + (nRows - 1 - cell.pcIdx) * step}
            width={Math.max(1, x1 - x0 + 0.5)}
            height={step + 0.5}
            fill={cell.fill}
          />
        );
      })}

      {/* Chord-change vertical dividers */}
      {chordDividers.map((sec) => {
        const sx = Number(xScale(sec) ?? 0);
        return (
          <line
            key={sec}
            x1={sx}
            y1={top}
            x2={sx}
            y2={top + gH}
            stroke={divColor}
            strokeWidth={2.5}
          />
        );
      })}

      {/* Chord section headers */}
      {chordSpans.map((c) => {
        const midSec = (c.startSec + c.endSec) / 2;
        return (
          <text
            key={`${c.label}-${c.startSec}`}
            x={Number(xScale(midSec) ?? 0)}
            y={top - 12}
            textAnchor="middle"
            fontSize={14}
            fontWeight={600}
            fill={t.inkSoft}
            fontFamily={FONT}
          >
            {c.label}
          </text>
        );
      })}

      {/* Sequential energy colorbar */}
      <rect x={cbX} y={top} width={cbW} height={gH} fill="url(#cbGrad)" rx={2} />
      <text
        x={cbX + cbW / 2}
        y={top - 8}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        1.0
      </text>
      <text
        x={cbX + cbW / 2}
        y={top + gH + 18}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        0.0
      </text>
      <text
        x={cbX + cbW + 20}
        y={top + gH / 2}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
        fontFamily={FONT}
        transform={`rotate(90, ${cbX + cbW + 20}, ${top + gH / 2})`}
      >
        {COLORBAR_LABEL}
      </text>
    </g>
  );
}

export default function Chart() {
  const chordProgressionText = chordSpans.map((c) => c.label).join(" → ");
  const subtitle = `${SUBTITLE_PREFIX} · ${chordProgressionText} (${uniqueTimes.length} frames)`;

  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      skipAnimation
      xAxis={[
        {
          scaleType: "linear",
          min: minTimeSec,
          max: maxTimeSec,
          height: 56,
          label: X_AXIS_LABEL,
          valueFormatter: (v: number) => `${v.toFixed(1)}s`,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: [...pitchOrder].reverse(),
          width: 82,
          label: Y_AXIS_LABEL,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
        },
      ]}
      margin={{ left: 20, right: 96, top: 112, bottom: 24 }}
    >
      <text
        x={width / 2}
        y={38}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
        fontFamily={FONT}
      >
        {TITLE}
      </text>
      <text
        x={width / 2}
        y={64}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        {subtitle}
      </text>
      <ChromagramLayer />
      <ChartsXAxis />
      <ChartsYAxis />
    </ChartsContainer>
  );
}
