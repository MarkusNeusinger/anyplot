// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-25
//# anyplot-orientation: square
// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// Classic Sudoku starting puzzle — 0 = empty cell
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

  // Inner cell division lines (thin, drawn first)
  const thinLines = [];
  for (let i = 1; i <= 8; i++) {
    if (i % 3 === 0) continue;
    thinLines.push(
      <line key={`v${i}`}
        x1={gx + i * cell} y1={gy}
        x2={gx + i * cell} y2={gy + gridSize}
        stroke={t.inkSoft} strokeWidth={THIN}
      />,
      <line key={`h${i}`}
        x1={gx} y1={gy + i * cell}
        x2={gx + gridSize} y2={gy + i * cell}
        stroke={t.inkSoft} strokeWidth={THIN}
      />
    );
  }

  // 3×3 box boundary lines (thick, drawn on top of thin lines)
  const thickLines = [];
  for (let i = 0; i <= 9; i += 3) {
    thickLines.push(
      <line key={`bv${i}`}
        x1={gx + i * cell} y1={gy}
        x2={gx + i * cell} y2={gy + gridSize}
        stroke={t.ink} strokeWidth={THICK}
      />,
      <line key={`bh${i}`}
        x1={gx} y1={gy + i * cell}
        x2={gx + gridSize} y2={gy + i * cell}
        stroke={t.ink} strokeWidth={THICK}
      />
    );
  }

  // Given numbers centered in their cells
  const numbers = PUZZLE.flatMap((row, r) =>
    row.map((val, c) => {
      if (val === 0) return null;
      return (
        <text
          key={`n${r}${c}`}
          x={gx + c * cell + cell / 2}
          y={gy + r * cell + cell / 2}
          textAnchor="middle"
          dominantBaseline="central"
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
    <svg
      width={W}
      height={H}
      style={{ display: "block", background: t.pageBg }}
    >
      {/* Title */}
      <text
        x={W / 2}
        y={titleH / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={22}
        fontFamily='"Helvetica Neue", Helvetica, Arial, sans-serif'
        fill={t.ink}
      >
        sudoku-basic · javascript · muix · anyplot.ai
      </text>

      {/* Grid background */}
      <rect x={gx} y={gy} width={gridSize} height={gridSize} fill={t.pageBg} />

      {/* Cell dividers */}
      {thinLines}

      {/* Box borders */}
      {thickLines}

      {/* Given numbers */}
      {numbers}
    </svg>
  );
}
