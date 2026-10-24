// anyplot.ai
// piano-roll-midi: MIDI Piano Roll Visualization
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24

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
const MIN_PITCH_PAD_SEMITONES = 2;
const BEAT_PAD_SHARE = 0.012;
const TIME_AXIS_TITLE = "Time (measures)";
const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const BLACK_SEMITONES = [1, 3, 6, 8, 10];

// Columns: set these to your data's column names
const START = "Onset (beats)"; // role: start
const DURATION = "Duration (beats)"; // role: duration
const PITCH = "Pitch (MIDI note)"; // role: y
const VELOCITY = "Velocity"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, number>> = [
  // Measure 1 (C major)
  { [START]: 0, [DURATION]: 4, [PITCH]: 48, [VELOCITY]: 78 },
  { [START]: 0, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 58 },
  { [START]: 0, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 58 },
  { [START]: 0, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 58 },
  { [START]: 2, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 64 },
  { [START]: 2, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 64 },
  { [START]: 2, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 64 },
  { [START]: 0, [DURATION]: 1, [PITCH]: 72, [VELOCITY]: 88 },
  { [START]: 1, [DURATION]: 1, [PITCH]: 74, [VELOCITY]: 82 },
  { [START]: 2, [DURATION]: 0.5, [PITCH]: 72, [VELOCITY]: 88 },
  { [START]: 2.5, [DURATION]: 0.5, [PITCH]: 71, [VELOCITY]: 82 },
  { [START]: 3, [DURATION]: 1, [PITCH]: 69, [VELOCITY]: 88 },

  // Measure 2 (C major)
  { [START]: 4, [DURATION]: 4, [PITCH]: 48, [VELOCITY]: 81 },
  { [START]: 4, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 60 },
  { [START]: 4, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 60 },
  { [START]: 4, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 60 },
  { [START]: 6, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 66 },
  { [START]: 6, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 66 },
  { [START]: 6, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 66 },
  { [START]: 4, [DURATION]: 1, [PITCH]: 72, [VELOCITY]: 91 },
  { [START]: 5, [DURATION]: 1, [PITCH]: 74, [VELOCITY]: 85 },
  { [START]: 6, [DURATION]: 0.5, [PITCH]: 72, [VELOCITY]: 91 },
  { [START]: 6.5, [DURATION]: 0.5, [PITCH]: 71, [VELOCITY]: 85 },
  { [START]: 7, [DURATION]: 1, [PITCH]: 69, [VELOCITY]: 91 },

  // Measure 3 (A minor)
  { [START]: 8, [DURATION]: 4, [PITCH]: 45, [VELOCITY]: 84 },
  { [START]: 8, [DURATION]: 2, [PITCH]: 57, [VELOCITY]: 62 },
  { [START]: 8, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 62 },
  { [START]: 8, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 62 },
  { [START]: 10, [DURATION]: 2, [PITCH]: 57, [VELOCITY]: 68 },
  { [START]: 10, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 68 },
  { [START]: 10, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 68 },
  { [START]: 8, [DURATION]: 1, [PITCH]: 69, [VELOCITY]: 94 },
  { [START]: 9, [DURATION]: 1, [PITCH]: 71, [VELOCITY]: 88 },
  { [START]: 10, [DURATION]: 0.5, [PITCH]: 69, [VELOCITY]: 94 },
  { [START]: 10.5, [DURATION]: 0.5, [PITCH]: 67, [VELOCITY]: 88 },
  { [START]: 11, [DURATION]: 1, [PITCH]: 65, [VELOCITY]: 94 },

  // Measure 4 (A minor)
  { [START]: 12, [DURATION]: 4, [PITCH]: 45, [VELOCITY]: 87 },
  { [START]: 12, [DURATION]: 2, [PITCH]: 57, [VELOCITY]: 64 },
  { [START]: 12, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 64 },
  { [START]: 12, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 64 },
  { [START]: 14, [DURATION]: 2, [PITCH]: 57, [VELOCITY]: 70 },
  { [START]: 14, [DURATION]: 2, [PITCH]: 60, [VELOCITY]: 70 },
  { [START]: 14, [DURATION]: 2, [PITCH]: 64, [VELOCITY]: 70 },
  { [START]: 12, [DURATION]: 1, [PITCH]: 69, [VELOCITY]: 97 },
  { [START]: 13, [DURATION]: 1, [PITCH]: 71, [VELOCITY]: 91 },
  { [START]: 14, [DURATION]: 0.5, [PITCH]: 69, [VELOCITY]: 97 },
  { [START]: 14.5, [DURATION]: 0.5, [PITCH]: 67, [VELOCITY]: 91 },
  { [START]: 15, [DURATION]: 1, [PITCH]: 65, [VELOCITY]: 97 },

  // Measure 5 (F major)
  { [START]: 16, [DURATION]: 4, [PITCH]: 53, [VELOCITY]: 90 },
  { [START]: 16, [DURATION]: 2, [PITCH]: 65, [VELOCITY]: 66 },
  { [START]: 16, [DURATION]: 2, [PITCH]: 69, [VELOCITY]: 66 },
  { [START]: 16, [DURATION]: 2, [PITCH]: 72, [VELOCITY]: 66 },
  { [START]: 18, [DURATION]: 2, [PITCH]: 65, [VELOCITY]: 72 },
  { [START]: 18, [DURATION]: 2, [PITCH]: 69, [VELOCITY]: 72 },
  { [START]: 18, [DURATION]: 2, [PITCH]: 72, [VELOCITY]: 72 },
  { [START]: 16, [DURATION]: 1, [PITCH]: 74, [VELOCITY]: 100 },
  { [START]: 17, [DURATION]: 1, [PITCH]: 76, [VELOCITY]: 94 },
  { [START]: 18, [DURATION]: 0.5, [PITCH]: 74, [VELOCITY]: 100 },
  { [START]: 18.5, [DURATION]: 0.5, [PITCH]: 74, [VELOCITY]: 94 },
  { [START]: 19, [DURATION]: 1, [PITCH]: 71, [VELOCITY]: 100 },

  // Measure 6 (F major)
  { [START]: 20, [DURATION]: 4, [PITCH]: 53, [VELOCITY]: 93 },
  { [START]: 20, [DURATION]: 2, [PITCH]: 65, [VELOCITY]: 68 },
  { [START]: 20, [DURATION]: 2, [PITCH]: 69, [VELOCITY]: 68 },
  { [START]: 20, [DURATION]: 2, [PITCH]: 72, [VELOCITY]: 68 },
  { [START]: 22, [DURATION]: 2, [PITCH]: 65, [VELOCITY]: 74 },
  { [START]: 22, [DURATION]: 2, [PITCH]: 69, [VELOCITY]: 74 },
  { [START]: 22, [DURATION]: 2, [PITCH]: 72, [VELOCITY]: 74 },
  { [START]: 20, [DURATION]: 1, [PITCH]: 74, [VELOCITY]: 103 },
  { [START]: 21, [DURATION]: 1, [PITCH]: 76, [VELOCITY]: 97 },
  { [START]: 22, [DURATION]: 0.5, [PITCH]: 74, [VELOCITY]: 103 },
  { [START]: 22.5, [DURATION]: 0.5, [PITCH]: 74, [VELOCITY]: 97 },
  { [START]: 23, [DURATION]: 1, [PITCH]: 71, [VELOCITY]: 103 },

  // Measure 7 (G major)
  { [START]: 24, [DURATION]: 4, [PITCH]: 55, [VELOCITY]: 96 },
  { [START]: 24, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 70 },
  { [START]: 24, [DURATION]: 2, [PITCH]: 71, [VELOCITY]: 70 },
  { [START]: 24, [DURATION]: 2, [PITCH]: 74, [VELOCITY]: 70 },
  { [START]: 26, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 76 },
  { [START]: 26, [DURATION]: 2, [PITCH]: 71, [VELOCITY]: 76 },
  { [START]: 26, [DURATION]: 2, [PITCH]: 74, [VELOCITY]: 76 },
  { [START]: 24, [DURATION]: 1, [PITCH]: 76, [VELOCITY]: 106 },
  { [START]: 25, [DURATION]: 1, [PITCH]: 77, [VELOCITY]: 100 },
  { [START]: 26, [DURATION]: 0.5, [PITCH]: 76, [VELOCITY]: 106 },
  { [START]: 26.5, [DURATION]: 0.5, [PITCH]: 69, [VELOCITY]: 100 },
  { [START]: 27, [DURATION]: 1, [PITCH]: 72, [VELOCITY]: 106 },

  // Measure 8 (G major)
  { [START]: 28, [DURATION]: 4, [PITCH]: 55, [VELOCITY]: 99 },
  { [START]: 28, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 72 },
  { [START]: 28, [DURATION]: 2, [PITCH]: 71, [VELOCITY]: 72 },
  { [START]: 28, [DURATION]: 2, [PITCH]: 74, [VELOCITY]: 72 },
  { [START]: 30, [DURATION]: 2, [PITCH]: 67, [VELOCITY]: 78 },
  { [START]: 30, [DURATION]: 2, [PITCH]: 71, [VELOCITY]: 78 },
  { [START]: 30, [DURATION]: 2, [PITCH]: 74, [VELOCITY]: 78 },
  { [START]: 28, [DURATION]: 1, [PITCH]: 76, [VELOCITY]: 109 },
  { [START]: 29, [DURATION]: 1, [PITCH]: 77, [VELOCITY]: 103 },
  { [START]: 30, [DURATION]: 0.5, [PITCH]: 76, [VELOCITY]: 109 },
  { [START]: 30.5, [DURATION]: 0.5, [PITCH]: 69, [VELOCITY]: 103 },
  { [START]: 31, [DURATION]: 1, [PITCH]: 72, [VELOCITY]: 109 },
];

// Plot: reads only data and the constants above
const pitches = data.map((n) => n[PITCH]);
const velocities = data.map((n) => n[VELOCITY]);
const endBeats = data.map((n) => n[START] + n[DURATION]);
const totalBeats = Math.max(...endBeats);
const measures = Math.ceil(totalBeats / BEATS_PER_MEASURE);

const minPitch = Math.min(...pitches);
const maxPitch = Math.max(...pitches);
const pitchPad = Math.max(
  MIN_PITCH_PAD_SEMITONES,
  Math.round((maxPitch - minPitch) * PITCH_PAD_SHARE),
);
const pitchAxisMin = minPitch - pitchPad;
const pitchAxisMax = maxPitch + pitchPad;

const velocityMin = Math.min(...velocities);
const velocityMax = Math.max(...velocities);
const velocitySpan = velocityMax - velocityMin;

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

const seq0Num = parseInt(t.seq[0].replace("#", ""), 16);
const seq1Num = parseInt(t.seq[1].replace("#", ""), 16);
const r0 = (seq0Num >> 16) & 255;
const g0 = (seq0Num >> 8) & 255;
const b0 = seq0Num & 255;
const r1 = (seq1Num >> 16) & 255;
const g1 = (seq1Num >> 8) & 255;
const b1 = seq1Num & 255;

const noteFills = data.map((row) => {
  const ratio = (row[VELOCITY] - velocityMin) / velocitySpan;
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

      {data.map((row, i) => {
        const x0 = xScale(row[START]);
        const x1 = xScale(row[START] + row[DURATION]);
        const rowTop = yScale(row[PITCH] + 0.5);
        const rowBottom = yScale(row[PITCH] - 0.5);
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
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: "14px",
          height: "32px",
        }}
      >
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1 }}>
          {TITLE}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Typography sx={{ fontSize: 14, color: t.inkSoft, lineHeight: 1 }}>
            {`${VELOCITY}: Soft (${velocityMin})`}
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
            label: TIME_AXIS_TITLE,
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
            valueFormatter: (pitch: number) => noteNameByPitch[Math.round(pitch)],
            label: PITCH,
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
