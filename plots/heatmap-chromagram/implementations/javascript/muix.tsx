// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const { width, height } = window.ANYPLOT_SIZE;
const TITLE = "heatmap-chromagram · javascript · muix · anyplot.ai";
const FONT = "Inter, system-ui, sans-serif";
const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const ENERGY_MIN = 0;
const ENERGY_MAX = 1;

// Columns: set these to your data's column names
const TIME = "Time (s)"; // role: time
const PITCH_CLASS = "Pitch class"; // role: pitch_class
const ENERGY = "Energy"; // role: energy
const CHORD = "Chord";

// Data: replace this block with your own records
const N_FRAMES = 80;
const SEC_PER_FRAME = 0.05;

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
    const energy = Number(Math.min(ENERGY_MAX, rawEnergy).toFixed(4));
    const timeSec = Number((f * SEC_PER_FRAME).toFixed(3));
    data.push({
      [TIME]: timeSec,
      [PITCH_CLASS]: pitchName,
      [ENERGY]: energy,
      [CHORD]: chord.label,
    });
  }
}

// Plot: reads only data and the constants above
const pitchOrder = Array.from(new Set(data.map((r) => String(r[PITCH_CLASS]))));
const pitchIndexMap = new Map<string, number>(pitchOrder.map((p, idx) => [p, idx]));
const uniqueTimes = Array.from(new Set(data.map((r) => Number(r[TIME])))).sort((a, b) => a - b);
const frameStepSec = uniqueTimes[1] - uniqueTimes[0];
const minTimeSec = uniqueTimes[0];
const maxTimeSec = uniqueTimes[uniqueTimes.length - 1] + frameStepSec;
const timeUnitMatch = TIME.match(/\(([^)]+)\)/);
const timeUnit = timeUnitMatch ? timeUnitMatch[1] : "";

const timeToChord = new Map<number, string>();
for (const r of data) {
  const tVal = Number(r[TIME]);
  if (!timeToChord.has(tVal)) {
    timeToChord.set(tVal, String(r[CHORD]));
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
  const timeSec = Number(row[TIME]);
  const pitch = String(row[PITCH_CLASS]);
  const pcIdx = pitchIndexMap.get(pitch)!;
  const val = Number(row[ENERGY]);
  const norm = (val - ENERGY_MIN) / (ENERGY_MAX - ENERGY_MIN);
  const r = Math.round(r1 + (r2 - r1) * norm);
  const g = Math.round(g1 + (g2 - g1) * norm);
  const b = Math.round(b1 + (b2 - b1) * norm);
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
  const xScale = useXScale() as (v: number) => number;

  const nRows = pitchOrder.length;
  const step = gH / nRows;
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
        const x0 = xScale(cell.timeSec);
        const x1 = xScale(cell.nextTimeSec);
        return (
          <rect
            key={cell.key}
            x={x0}
            y={top + (nRows - 1 - cell.pcIdx) * step}
            width={x1 - x0 + 0.5}
            height={step + 0.5}
            fill={cell.fill}
          />
        );
      })}

      {/* Chord-change vertical dividers */}
      {chordDividers.map((sec) => {
        const sx = xScale(sec);
        return (
          <line
            key={sec}
            x1={sx}
            y1={top}
            x2={sx}
            y2={top + gH}
            stroke={t.ink}
            strokeOpacity={0.45}
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
            x={xScale(midSec)}
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
        {ENERGY_MAX.toFixed(1)}
      </text>
      <text
        x={cbX + cbW / 2}
        y={top + gH + 18}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        {ENERGY_MIN.toFixed(1)}
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
        {ENERGY}
      </text>
    </g>
  );
}

export default function Chart() {
  const chordProgressionText = chordSpans.map((c) => c.label).join(" → ");
  const subtitle = `${ENERGY} across ${pitchOrder.length} ${PITCH_CLASS}es · ${chordProgressionText} (${uniqueTimes.length} frames)`;

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
          label: TIME,
          valueFormatter: (v: number) => `${v.toFixed(1)}${timeUnit}`,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: [...pitchOrder].reverse(),
          width: 82,
          label: PITCH_CLASS,
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
