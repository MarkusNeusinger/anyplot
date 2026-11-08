// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: muix 9.17.0 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-25
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const EMPTY = 0; // the value that marks a cell without a given
const THIN = 1; // cell line width (px)
const THICK = 4; // box border width (px)
const DIGIT_SHARE = 0.56; // digit height as a share of the cell side
const HEADER_H = 96;
const PAD = 40;

// Data: the puzzle's givens row by row from the top, 0 marks an empty cell
const GRID = [
  [5, 3, 0, 0, 7, 0, 0, 0, 0],
  [6, 0, 0, 1, 9, 5, 0, 0, 0],
  [0, 9, 8, 0, 0, 0, 0, 6, 0],
  [8, 0, 0, 0, 6, 0, 0, 0, 3],
  [4, 0, 0, 8, 0, 3, 0, 0, 1],
  [7, 0, 0, 0, 2, 0, 0, 0, 6],
  [0, 6, 0, 0, 0, 0, 2, 8, 0],
  [0, 0, 0, 4, 1, 9, 0, 0, 5],
  [0, 0, 0, 0, 8, 0, 0, 7, 9],
]; // role: grid

// Plot: reads only the grid and the constants above
const N = GRID.length;
const BOX = Math.round(Math.sqrt(N)); // a 9×9 grid splits into 3×3 boxes
const indices = Array.from({ length: N }, (_, i) => i);
const givens = GRID.flatMap((row, r) =>
  row.flatMap((value, c) => (value === EMPTY ? [] : [{ id: `${r}-${c}`, r, c, value }])),
);
const boundaries = Array.from({ length: N + 1 }, (_, i) => i);
// thin cell lines first, so the thick box borders paint over them where they meet
const lineLayers = [
  { id: "cells", at: boundaries.filter((i) => i % BOX !== 0), width: THIN, stroke: t.inkSoft },
  { id: "boxes", at: boundaries.filter((i) => i % BOX === 0), width: THICK, stroke: t.ink },
];

const TITLE = "sudoku-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${N} × ${N} grid in ${BOX} × ${BOX} boxes · ${givens.length} givens · ${N * N - givens.length} empty cells`;

function GridLayer() {
  const xScale = useXScale("col");
  const yScale = useYScale("row");
  const { left, top, width, height } = useDrawingArea();
  const cell = xScale.bandwidth();

  return (
    <g>
      {lineLayers.map((layer) => (
        <g key={layer.id} stroke={layer.stroke} strokeWidth={layer.width} strokeLinecap="square">
          {layer.at.map((i) => (
            <g key={i}>
              <line x1={left + i * cell} y1={top} x2={left + i * cell} y2={top + height} />
              <line x1={left} y1={top + i * cell} x2={left + width} y2={top + i * cell} />
            </g>
          ))}
        </g>
      ))}
      {givens.map((g) => (
        <text
          key={g.id}
          x={(xScale(g.c) ?? 0) + cell / 2}
          y={(yScale(g.r) ?? 0) + cell / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={cell * DIGIT_SHARE}
          fontWeight={600}
          fill={t.ink}
        >
          {g.value}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width, height - HEADER_H);

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsContainer
        width={side}
        height={side}
        margin={{ top: PAD, right: PAD, bottom: PAD, left: PAD }}
        skipAnimation
        series={[]}
        xAxis={[{ id: "col", scaleType: "band", data: indices, categoryGapRatio: 0, position: "none" }]}
        yAxis={[{ id: "row", scaleType: "band", data: indices, categoryGapRatio: 0, position: "none" }]}
      >
        <GridLayer />
      </ChartsContainer>
    </Box>
  );
}
