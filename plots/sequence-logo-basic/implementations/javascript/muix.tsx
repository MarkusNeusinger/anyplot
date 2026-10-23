// anyplot.ai
// sequence-logo-basic: Sequence Logo for Motif Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const LETTER_COLOR: Record<string, string> = {
  A: t.palette[0], // #009E73
  C: t.palette[2], // #4467A3
  G: t.palette[3], // #BD8233
  T: t.palette[4], // #AE3030
};

// Columns: set these to your data's column names
const POSITION = "Position"; // role: position
const LETTER = "Nucleotide"; // role: letter
const FREQUENCY = "Frequency"; // role: frequency

// Data: replace this block with your own records, one object per row
const data = [
  { [POSITION]: 1, [LETTER]: "A", [FREQUENCY]: 0.3 },
  { [POSITION]: 1, [LETTER]: "C", [FREQUENCY]: 0.25 },
  { [POSITION]: 1, [LETTER]: "G", [FREQUENCY]: 0.2 },
  { [POSITION]: 1, [LETTER]: "T", [FREQUENCY]: 0.25 },
  { [POSITION]: 2, [LETTER]: "A", [FREQUENCY]: 0.15 },
  { [POSITION]: 2, [LETTER]: "C", [FREQUENCY]: 0.55 },
  { [POSITION]: 2, [LETTER]: "G", [FREQUENCY]: 0.1 },
  { [POSITION]: 2, [LETTER]: "T", [FREQUENCY]: 0.2 },
  { [POSITION]: 3, [LETTER]: "A", [FREQUENCY]: 0.05 },
  { [POSITION]: 3, [LETTER]: "C", [FREQUENCY]: 0.05 },
  { [POSITION]: 3, [LETTER]: "G", [FREQUENCY]: 0.05 },
  { [POSITION]: 3, [LETTER]: "T", [FREQUENCY]: 0.85 },
  { [POSITION]: 4, [LETTER]: "A", [FREQUENCY]: 0.9 },
  { [POSITION]: 4, [LETTER]: "C", [FREQUENCY]: 0.04 },
  { [POSITION]: 4, [LETTER]: "G", [FREQUENCY]: 0.03 },
  { [POSITION]: 4, [LETTER]: "T", [FREQUENCY]: 0.03 },
  { [POSITION]: 5, [LETTER]: "A", [FREQUENCY]: 0.04 },
  { [POSITION]: 5, [LETTER]: "C", [FREQUENCY]: 0.04 },
  { [POSITION]: 5, [LETTER]: "G", [FREQUENCY]: 0.88 },
  { [POSITION]: 5, [LETTER]: "T", [FREQUENCY]: 0.04 },
  { [POSITION]: 6, [LETTER]: "A", [FREQUENCY]: 0.03 },
  { [POSITION]: 6, [LETTER]: "C", [FREQUENCY]: 0.9 },
  { [POSITION]: 6, [LETTER]: "G", [FREQUENCY]: 0.04 },
  { [POSITION]: 6, [LETTER]: "T", [FREQUENCY]: 0.03 },
  { [POSITION]: 7, [LETTER]: "A", [FREQUENCY]: 0.05 },
  { [POSITION]: 7, [LETTER]: "C", [FREQUENCY]: 0.05 },
  { [POSITION]: 7, [LETTER]: "G", [FREQUENCY]: 0.85 },
  { [POSITION]: 7, [LETTER]: "T", [FREQUENCY]: 0.05 },
  { [POSITION]: 8, [LETTER]: "A", [FREQUENCY]: 0.7 },
  { [POSITION]: 8, [LETTER]: "C", [FREQUENCY]: 0.1 },
  { [POSITION]: 8, [LETTER]: "G", [FREQUENCY]: 0.12 },
  { [POSITION]: 8, [LETTER]: "T", [FREQUENCY]: 0.08 },
  { [POSITION]: 9, [LETTER]: "A", [FREQUENCY]: 0.2 },
  { [POSITION]: 9, [LETTER]: "C", [FREQUENCY]: 0.3 },
  { [POSITION]: 9, [LETTER]: "G", [FREQUENCY]: 0.3 },
  { [POSITION]: 9, [LETTER]: "T", [FREQUENCY]: 0.2 },
  { [POSITION]: 10, [LETTER]: "A", [FREQUENCY]: 0.25 },
  { [POSITION]: 10, [LETTER]: "C", [FREQUENCY]: 0.25 },
  { [POSITION]: 10, [LETTER]: "G", [FREQUENCY]: 0.25 },
  { [POSITION]: 10, [LETTER]: "T", [FREQUENCY]: 0.25 },
];

// Plot: reads only data and the constants above
const positions = Array.from(new Set(data.map((d) => `${d[POSITION]}`)));
const letters = Array.from(new Set(data.map((d) => d[LETTER])));
const MAX_BITS = Math.log2(letters.length);

const STACKS = positions.map((posLabel) => {
  const rows = data.filter((d) => `${d[POSITION]}` === posLabel);
  const entropy = rows.reduce((bits, r) => {
    const p = r[FREQUENCY];
    return p > 0 ? bits - p * Math.log2(p) : bits;
  }, 0);
  const ic = MAX_BITS - entropy;
  const sorted = [...rows].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);
  let cumulative = 0;
  return sorted
    .filter((r) => r[FREQUENCY] > 0)
    .map((r) => {
      const bits = r[FREQUENCY] * ic;
      const letter = r[LETTER];
      const segment = {
        letter,
        from: cumulative,
        to: cumulative + bits,
        color:
          LETTER_COLOR[letter] ??
          t.palette[letters.indexOf(letter) % t.palette.length],
      };
      cumulative += bits;
      return segment;
    });
});

const CAP_HEIGHT_RATIO = 0.72;
const VERTICAL_STRETCH = 1 / CAP_HEIGHT_RATIO;

function SequenceLogoGlyphs() {
  const xScale = useXScale() as any;
  const yScale = useYScale() as any;
  const bandwidth = xScale.bandwidth();
  const paddingX = bandwidth * 0.08;
  const usableWidth = bandwidth - 2 * paddingX;

  return (
    <g>
      {STACKS.map((segments, posIndex) =>
        segments.map((seg) => {
          const xLeft = xScale(positions[posIndex]) + paddingX;
          const yBottom = yScale(seg.from);
          const yTop = yScale(seg.to);
          const heightPx = yBottom - yTop;
          if (heightPx < 1.5) return null;
          const translateY = yBottom * (1 - VERTICAL_STRETCH);
          return (
            <text
              key={`${posIndex}-${seg.letter}`}
              x={xLeft + usableWidth / 2}
              y={yBottom}
              textAnchor="middle"
              textLength={usableWidth}
              lengthAdjust="spacingAndGlyphs"
              fontSize={heightPx}
              fontWeight={700}
              fontFamily="Arial, Liberation Sans, DejaVu Sans, sans-serif"
              fill={seg.color}
              transform={`translate(0 ${translateY}) scale(1 ${VERTICAL_STRETCH})`}
            >
              {seg.letter}
            </text>
          );
        }),
      )}
    </g>
  );
}

const TITLE_H = 56;

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          height: TITLE_H,
          lineHeight: `${TITLE_H}px`,
          flexShrink: 0,
        }}
      >
        sequence-logo-basic · javascript · muix · anyplot.ai
      </Typography>
      <ChartsContainer
        width={W}
        height={H - TITLE_H}
        series={[]}
        margin={{ top: 30, right: 40, bottom: 20, left: 20 }}
        xAxis={[
          {
            scaleType: "band",
            data: positions,
            height: 64,
            label: POSITION,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: MAX_BITS,
            width: 84,
            label: "Information content (bits)",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft, strokeWidth: 1 },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <SequenceLogoGlyphs />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
