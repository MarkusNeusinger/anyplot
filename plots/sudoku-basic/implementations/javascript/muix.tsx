//# anyplot-orientation: square
// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Classic Sudoku puzzle — 0 = empty cell
const PUZZLE = [
  [5, 3, 0, 0, 7, 0, 0, 0, 0],
  [6, 0, 0, 1, 9, 5, 0, 0, 0],
  [0, 9, 8, 0, 0, 0, 0, 6, 0],
  [8, 0, 0, 0, 6, 0, 0, 0, 3],
  [4, 0, 0, 8, 0, 3, 0, 0, 1],
  [7, 0, 0, 0, 2, 0, 0, 0, 6],
  [0, 6, 0, 0, 0, 0, 2, 8, 0],
  [0, 0, 0, 4, 1, 9, 0, 0, 5],
  [0, 0, 0, 0, 8, 0, 0, 7, 9],
];

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const titleH = 70;
  const pad = 50;
  const gridSize = Math.min(W - 2 * pad, H - titleH - 2 * pad);
  const cell = gridSize / 9;
  const gx = (W - gridSize) / 2;
  const gy = titleH + (H - titleH - gridSize) / 2;

  const THIN = 0.7;
  const THICK = 3;

  // Inner cell division lines (thin)
  const thinLines = [];
  for (let i = 1; i <= 8; i++) {
    if (i % 3 === 0) continue;
    thinLines.push(
      <line key={`v${i}`} x1={i * cell} y1={0} x2={i * cell} y2={gridSize}
        stroke={t.inkSoft} strokeWidth={THIN} />,
      <line key={`h${i}`} x1={0} y1={i * cell} x2={gridSize} y2={i * cell}
        stroke={t.inkSoft} strokeWidth={THIN} />
    );
  }

  // 3×3 box boundary lines (thick)
  const thickLines = [];
  for (let i = 0; i <= 9; i += 3) {
    thickLines.push(
      <line key={`bv${i}`} x1={i * cell} y1={0} x2={i * cell} y2={gridSize}
        stroke={t.ink} strokeWidth={THICK} />,
      <line key={`bh${i}`} x1={0} y1={i * cell} x2={gridSize} y2={i * cell}
        stroke={t.ink} strokeWidth={THICK} />
    );
  }

  // Given numbers centered in their cells
  const numbers = PUZZLE.flatMap((row, r) =>
    row.map((val, c) => {
      if (val === 0) return null;
      return (
        <text key={`n${r}${c}`}
          x={c * cell + cell / 2} y={r * cell + cell / 2}
          textAnchor="middle" dominantBaseline="central"
          fontSize={cell * 0.52}
          fontFamily='"Helvetica Neue", Helvetica, Arial, sans-serif'
          fontWeight="700"
          fill={t.ink}
        >
          {val}
        </text>
      );
    })
  ).filter(Boolean);

  return (
    <Box
      sx={{
        position: "relative",
        width: W,
        height: H,
        bgcolor: t.pageBg,
        overflow: "hidden",
      }}
    >
      {/* MUI Typography for theme-aware title */}
      <Typography
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: titleH,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
          color: t.ink,
          lineHeight: 1,
          m: 0,
          p: 0,
        }}
      >
        sudoku-basic · javascript · muix · anyplot.ai
      </Typography>

      {/* SVG grid rendered via MUI Box component bridge */}
      <Box
        component="svg"
        sx={{ position: "absolute", top: gy, left: gx, display: "block" }}
        width={gridSize}
        height={gridSize}
      >
        <rect width={gridSize} height={gridSize} fill={t.pageBg} />
        {thinLines}
        {thickLines}
        {numbers}
      </Box>
    </Box>
  );
}
