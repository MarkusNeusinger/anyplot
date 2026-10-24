// anyplot.ai
// piano-roll-midi: MIDI Piano Roll Visualization
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-20

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "piano-roll-midi · javascript · muix · anyplot.ai";
const BEATS_PER_MEASURE = 4;
const PITCH_PAD_SHARE = 0.08;
const BEAT_PAD_SHARE = 0.012;
const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const BLACK_SEMITONES = [1, 3, 6, 8, 10];

const START_COL = "start_beat";
const DURATION_COL = "duration_beats";
const PITCH_COL = "midi_pitch";
const VELOCITY_COL = "velocity";

// Data: 8-measure C-major chord progression with bass, comping triads, and melody (flat scalar records)
const DATA: Array<Record<string, number>> = [
  // Measure 1 (C major)
  { start_beat: 0, duration_beats: 4, midi_pitch: 48, velocity: 78 },
  { start_beat: 0, duration_beats: 2, midi_pitch: 60, velocity: 58 },
  { start_beat: 0, duration_beats: 2, midi_pitch: 64, velocity: 58 },
  { start_beat: 0, duration_beats: 2, midi_pitch: 67, velocity: 58 },
  { start_beat: 2, duration_beats: 2, midi_pitch: 60, velocity: 64 },
  { start_beat: 2, duration_beats: 2, midi_pitch: 64, velocity: 64 },
  { start_beat: 2, duration_beats: 2, midi_pitch: 67, velocity: 64 },
  { start_beat: 0, duration_beats: 1, midi_pitch: 72, velocity: 88 },
  { start_beat: 1, duration_beats: 1, midi_pitch: 74, velocity: 82 },
  { start_beat: 2, duration_beats: 0.5, midi_pitch: 72, velocity: 88 },
  { start_beat: 2.5, duration_beats: 0.5, midi_pitch: 71, velocity: 82 },
  { start_beat: 3, duration_beats: 1, midi_pitch: 69, velocity: 88 },

  // Measure 2 (C major)
  { start_beat: 4, duration_beats: 4, midi_pitch: 48, velocity: 81 },
  { start_beat: 4, duration_beats: 2, midi_pitch: 60, velocity: 60 },
  { start_beat: 4, duration_beats: 2, midi_pitch: 64, velocity: 60 },
  { start_beat: 4, duration_beats: 2, midi_pitch: 67, velocity: 60 },
  { start_beat: 6, duration_beats: 2, midi_pitch: 60, velocity: 66 },
  { start_beat: 6, duration_beats: 2, midi_pitch: 64, velocity: 66 },
  { start_beat: 6, duration_beats: 2, midi_pitch: 67, velocity: 66 },
  { start_beat: 4, duration_beats: 1, midi_pitch: 72, velocity: 91 },
  { start_beat: 5, duration_beats: 1, midi_pitch: 74, velocity: 85 },
  { start_beat: 6, duration_beats: 0.5, midi_pitch: 72, velocity: 91 },
  { start_beat: 6.5, duration_beats: 0.5, midi_pitch: 71, velocity: 85 },
  { start_beat: 7, duration_beats: 1, midi_pitch: 69, velocity: 91 },

  // Measure 3 (A minor)
  { start_beat: 8, duration_beats: 4, midi_pitch: 45, velocity: 84 },
  { start_beat: 8, duration_beats: 2, midi_pitch: 57, velocity: 62 },
  { start_beat: 8, duration_beats: 2, midi_pitch: 60, velocity: 62 },
  { start_beat: 8, duration_beats: 2, midi_pitch: 64, velocity: 62 },
  { start_beat: 10, duration_beats: 2, midi_pitch: 57, velocity: 68 },
  { start_beat: 10, duration_beats: 2, midi_pitch: 60, velocity: 68 },
  { start_beat: 10, duration_beats: 2, midi_pitch: 64, velocity: 68 },
  { start_beat: 8, duration_beats: 1, midi_pitch: 69, velocity: 94 },
  { start_beat: 9, duration_beats: 1, midi_pitch: 71, velocity: 88 },
  { start_beat: 10, duration_beats: 0.5, midi_pitch: 69, velocity: 94 },
  { start_beat: 10.5, duration_beats: 0.5, midi_pitch: 67, velocity: 88 },
  { start_beat: 11, duration_beats: 1, midi_pitch: 65, velocity: 94 },

  // Measure 4 (A minor)
  { start_beat: 12, duration_beats: 4, midi_pitch: 45, velocity: 87 },
  { start_beat: 12, duration_beats: 2, midi_pitch: 57, velocity: 64 },
  { start_beat: 12, duration_beats: 2, midi_pitch: 60, velocity: 64 },
  { start_beat: 12, duration_beats: 2, midi_pitch: 64, velocity: 64 },
  { start_beat: 14, duration_beats: 2, midi_pitch: 57, velocity: 70 },
  { start_beat: 14, duration_beats: 2, midi_pitch: 60, velocity: 70 },
  { start_beat: 14, duration_beats: 2, midi_pitch: 64, velocity: 70 },
  { start_beat: 12, duration_beats: 1, midi_pitch: 69, velocity: 97 },
  { start_beat: 13, duration_beats: 1, midi_pitch: 71, velocity: 91 },
  { start_beat: 14, duration_beats: 0.5, midi_pitch: 69, velocity: 97 },
  { start_beat: 14.5, duration_beats: 0.5, midi_pitch: 67, velocity: 91 },
  { start_beat: 15, duration_beats: 1, midi_pitch: 65, velocity: 97 },

  // Measure 5 (F major)
  { start_beat: 16, duration_beats: 4, midi_pitch: 53, velocity: 90 },
  { start_beat: 16, duration_beats: 2, midi_pitch: 65, velocity: 66 },
  { start_beat: 16, duration_beats: 2, midi_pitch: 69, velocity: 66 },
  { start_beat: 16, duration_beats: 2, midi_pitch: 72, velocity: 66 },
  { start_beat: 18, duration_beats: 2, midi_pitch: 65, velocity: 72 },
  { start_beat: 18, duration_beats: 2, midi_pitch: 69, velocity: 72 },
  { start_beat: 18, duration_beats: 2, midi_pitch: 72, velocity: 72 },
  { start_beat: 16, duration_beats: 1, midi_pitch: 74, velocity: 100 },
  { start_beat: 17, duration_beats: 1, midi_pitch: 76, velocity: 94 },
  { start_beat: 18, duration_beats: 0.5, midi_pitch: 74, velocity: 100 },
  { start_beat: 18.5, duration_beats: 0.5, midi_pitch: 74, velocity: 94 },
  { start_beat: 19, duration_beats: 1, midi_pitch: 71, velocity: 100 },

  // Measure 6 (F major)
  { start_beat: 20, duration_beats: 4, midi_pitch: 53, velocity: 93 },
  { start_beat: 20, duration_beats: 2, midi_pitch: 65, velocity: 68 },
  { start_beat: 20, duration_beats: 2, midi_pitch: 69, velocity: 68 },
  { start_beat: 20, duration_beats: 2, midi_pitch: 72, velocity: 68 },
  { start_beat: 22, duration_beats: 2, midi_pitch: 65, velocity: 74 },
  { start_beat: 22, duration_beats: 2, midi_pitch: 69, velocity: 74 },
  { start_beat: 22, duration_beats: 2, midi_pitch: 72, velocity: 74 },
  { start_beat: 20, duration_beats: 1, midi_pitch: 74, velocity: 103 },
  { start_beat: 21, duration_beats: 1, midi_pitch: 76, velocity: 97 },
  { start_beat: 22, duration_beats: 0.5, midi_pitch: 74, velocity: 103 },
  { start_beat: 22.5, duration_beats: 0.5, midi_pitch: 74, velocity: 97 },
  { start_beat: 23, duration_beats: 1, midi_pitch: 71, velocity: 103 },

  // Measure 7 (G major)
  { start_beat: 24, duration_beats: 4, midi_pitch: 55, velocity: 96 },
  { start_beat: 24, duration_beats: 2, midi_pitch: 67, velocity: 70 },
  { start_beat: 24, duration_beats: 2, midi_pitch: 71, velocity: 70 },
  { start_beat: 24, duration_beats: 2, midi_pitch: 74, velocity: 70 },
  { start_beat: 26, duration_beats: 2, midi_pitch: 67, velocity: 76 },
  { start_beat: 26, duration_beats: 2, midi_pitch: 71, velocity: 76 },
  { start_beat: 26, duration_beats: 2, midi_pitch: 74, velocity: 76 },
  { start_beat: 24, duration_beats: 1, midi_pitch: 76, velocity: 106 },
  { start_beat: 25, duration_beats: 1, midi_pitch: 77, velocity: 100 },
  { start_beat: 26, duration_beats: 0.5, midi_pitch: 76, velocity: 106 },
  { start_beat: 26.5, duration_beats: 0.5, midi_pitch: 69, velocity: 100 },
  { start_beat: 27, duration_beats: 1, midi_pitch: 72, velocity: 106 },

  // Measure 8 (G major)
  { start_beat: 28, duration_beats: 4, midi_pitch: 55, velocity: 99 },
  { start_beat: 28, duration_beats: 2, midi_pitch: 67, velocity: 72 },
  { start_beat: 28, duration_beats: 2, midi_pitch: 71, velocity: 72 },
  { start_beat: 28, duration_beats: 2, midi_pitch: 74, velocity: 72 },
  { start_beat: 30, duration_beats: 2, midi_pitch: 67, velocity: 78 },
  { start_beat: 30, duration_beats: 2, midi_pitch: 71, velocity: 78 },
  { start_beat: 30, duration_beats: 2, midi_pitch: 74, velocity: 78 },
  { start_beat: 28, duration_beats: 1, midi_pitch: 76, velocity: 109 },
  { start_beat: 29, duration_beats: 1, midi_pitch: 77, velocity: 103 },
  { start_beat: 30, duration_beats: 0.5, midi_pitch: 76, velocity: 109 },
  { start_beat: 30.5, duration_beats: 0.5, midi_pitch: 69, velocity: 103 },
  { start_beat: 31, duration_beats: 1, midi_pitch: 72, velocity: 109 },
];

const pitches = DATA.map((n) => n[PITCH_COL]);
const velocities = DATA.map((n) => n[VELOCITY_COL]);
const endBeats = DATA.map((n) => n[START_COL] + n[DURATION_COL]);
const totalBeats = Math.max(...endBeats);
const measures = Math.ceil(totalBeats / BEATS_PER_MEASURE);

const minPitch = Math.min(...pitches);
const maxPitch = Math.max(...pitches);
const pitchPad = Math.max(2, Math.round((maxPitch - minPitch) * PITCH_PAD_SHARE));
const pitchAxisMin = minPitch - pitchPad;
const pitchAxisMax = maxPitch + pitchPad;

const velocityMin = Math.min(...velocities);
const velocityMax = Math.max(...velocities);
const velocitySpan = velocityMax - velocityMin || 1;

const beatPad = totalBeats * BEAT_PAD_SHARE;
const measureTicks = Array.from({ length: measures }, (_, i) => i * BEATS_PER_MEASURE);
const octaveTicks: number[] = [];
const blackKeyPitches: number[] = [];
const noteNameByPitch: Record<number, string> = {};

for (let p = Math.ceil(pitchAxisMin); p <= Math.floor(pitchAxisMax); p += 1) {
  const semitone = ((p % 12) + 12) % 12;
  noteNameByPitch[p] = `${NOTE_NAMES[semitone]}${Math.floor(p / 12) - 1}`;
  if (semitone === 0) octaveTicks.push(p);
  if (BLACK_SEMITONES.includes(semitone)) blackKeyPitches.push(p);
}

// Parse sequential color endpoints for velocity interpolation
const seq0Num = parseInt(t.seq[0].replace("#", ""), 16);
const seq1Num = parseInt(t.seq[1].replace("#", ""), 16);
const r0 = (seq0Num >> 16) & 255;
const g0 = (seq0Num >> 8) & 255;
const b0 = seq0Num & 255;
const r1 = (seq1Num >> 16) & 255;
const g1 = (seq1Num >> 8) & 255;
const b1 = seq1Num & 255;

const noteFills = DATA.map((row) => {
  const ratio = (row[VELOCITY_COL] - velocityMin) / velocitySpan;
  const r = Math.round(r0 + (r1 - r0) * ratio);
  const g = Math.round(g0 + (g1 - g0) * ratio);
  const b = Math.round(b0 + (b1 - b0) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
});

const beats = Array.from({ length: totalBeats + 1 }, (_, b) => b);

function PianoRollOverlay() {
  const xScale = useXScale("beats") as unknown as (v: number) => number;
  const yScale = useYScale("pitch") as unknown as (v: number) => number;
  const drawingArea = useDrawingArea();

  return (
    <g>
      {/* Black-key row shading */}
      {blackKeyPitches.map((p) => (
        <rect
          key={`row-${p}`}
          x={drawingArea.left}
          y={yScale(p + 0.5)}
          width={drawingArea.width}
          height={Math.abs(yScale(p - 0.5) - yScale(p + 0.5))}
          fill={t.ink}
          fillOpacity={0.05}
        />
      ))}

      {/* Beat and measure grid lines */}
      {beats.map((b) => {
        const isMeasure = b % BEATS_PER_MEASURE === 0;
        return (
          <line
            key={`beat-${b}`}
            x1={xScale(b)}
            x2={xScale(b)}
            y1={drawingArea.top}
            y2={drawingArea.top + drawingArea.height}
            stroke={isMeasure ? t.ink : t.grid}
            strokeOpacity={isMeasure ? 0.28 : 1}
            strokeWidth={isMeasure ? 1.5 : 1}
          />
        );
      })}

      {/* Note bars */}
      {DATA.map((row, i) => {
        const x0 = xScale(row[START_COL]);
        const x1 = xScale(row[START_COL] + row[DURATION_COL]);
        const rowTop = yScale(row[PITCH_COL] + 0.5);
        const rowBottom = yScale(row[PITCH_COL] - 0.5);
        const pad = (rowBottom - rowTop) * 0.14;
        return (
          <rect
            key={`note-${i}`}
            x={x0 + 1}
            y={rowTop + pad}
            width={Math.max(x1 - x0 - 2, 3)}
            height={Math.max(rowBottom - rowTop - pad * 2, 2)}
            rx={3}
            fill={noteFills[i]}
            stroke={t.pageBg}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 24, right: 28, bottom: 20, left: 28 };
  const titleBlockHeight = 46;
  const chartWidth = size.width - padding.left - padding.right;
  const chartHeight = size.height - padding.top - padding.bottom - titleBlockHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        backgroundColor: t.pageBg,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: "14px", height: "32px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1 }}>
          {TITLE}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
            {`Velocity: Soft (${velocityMin})`}
          </Typography>
          <Box
            sx={{
              width: 180,
              height: 12,
              borderRadius: "4px",
              background: `linear-gradient(to right, ${t.seq[0]}, ${t.seq[1]})`,
              border: `1px solid ${t.grid}`,
            }}
          />
          <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
            {`Loud (${velocityMax})`}
          </Typography>
        </Box>
      </Box>
      <ChartsContainer
        width={chartWidth}
        height={chartHeight}
        series={[]}
        margin={{ left: 16, right: 24, top: 18, bottom: 12 }}
        xAxis={[
          {
            id: "beats",
            scaleType: "linear",
            min: -beatPad,
            max: totalBeats + beatPad,
            height: 54,
            tickInterval: measureTicks,
            valueFormatter: (beat: number) => `M${Math.round(beat / BEATS_PER_MEASURE) + 1}`,
            label: "Time (measures)",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "pitch",
            scaleType: "linear",
            min: pitchAxisMin,
            max: pitchAxisMax,
            width: 68,
            tickInterval: octaveTicks,
            valueFormatter: (pitch: number) => noteNameByPitch[Math.round(pitch)] ?? `${pitch}`,
            label: "Pitch",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        disableAxisListener
        skipAnimation
      >
        <PianoRollOverlay />
        <ChartsYAxis axisId="pitch" />
        <ChartsXAxis axisId="beats" />
      </ChartsContainer>
    </Box>
  );
}
