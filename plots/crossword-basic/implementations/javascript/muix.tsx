// anyplot.ai
// crossword-basic: Crossword Puzzle Grid
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// The puzzle is a monochrome print artefact: paper, ink and rules keep their values in both themes
const PAPER = "#FAF8F1";
const INK = "#1A1A17";
const RULE = "#4A4A44";
const BLOCK = "#"; // blocking-cell symbol in GRID; every other symbol is an entry cell
const NUMBER_SHARE = 0.3; // clue-number size as a share of the cell, leaves room for a letter
const HEADER_H = 84;
const BOARD_PAD = 28;

// Data: replace this block with your own parameters
// 15 × 15 newspaper-style grid, one string per row: "#" blocks, "." takes a letter
const GRID = [
  "....#.....#....",
  "....#.....#....",
  "....#.....#....",
  "##.............",
  "......##.......",
  "...#.......#...",
  "........#......",
  "##...#...#...##",
  "......#........",
  "...#.......#...",
  ".......##......",
  ".............##",
  "....#.....#....",
  "....#.....#....",
  "....#.....#....",
]; // role: grid

// Plot: reads only the parameters and the constants above
const rowCount = GRID.length;
const colCount = Math.max(...GRID.map((row) => row.length));
const isEntry = GRID.map((row) => Array.from({ length: colCount }, (_, c) => c < row.length && row[c] !== BLOCK));

// A cell gets the next clue number, in reading order, when it starts an across or a down word:
// open itself, closed (or the edge) before it and open after it
const cells: { r: number; c: number; entry: boolean; number: number | null }[] = [];
let nextNumber = 1;
let acrossCount = 0;
let downCount = 0;
for (let r = 0; r < rowCount; r += 1) {
  for (let c = 0; c < colCount; c += 1) {
    const entry = isEntry[r][c];
    const startsAcross = entry && !(isEntry[r][c - 1] ?? false) && (isEntry[r][c + 1] ?? false);
    const startsDown = entry && !(isEntry[r - 1]?.[c] ?? false) && (isEntry[r + 1]?.[c] ?? false);
    acrossCount += startsAcross ? 1 : 0;
    downCount += startsDown ? 1 : 0;
    cells.push({ r, c, entry, number: startsAcross || startsDown ? nextNumber++ : null });
  }
}
const blockCount = cells.filter((cell) => !cell.entry).length;
const symmetric = cells.every((cell) => cell.entry === isEntry[rowCount - 1 - cell.r][colCount - 1 - cell.c]);

// Square cells: the board takes the largest cell size that fits, centred in the drawing space
const { width: W, height: H } = window.ANYPLOT_SIZE;
const cellSize = Math.min((W - 2 * BOARD_PAD) / colCount, (H - HEADER_H - 2 * BOARD_PAD) / rowCount);
const marginX = (W - cellSize * colCount) / 2;
const marginY = (H - HEADER_H - cellSize * rowCount) / 2;
const columnKeys = Array.from({ length: colCount }, (_, c) => String(c));
const rowKeys = Array.from({ length: rowCount }, (_, r) => String(r));

const TITLE = "crossword-basic · javascript · muix · anyplot.ai";
const subtitle = `${rowCount} × ${colCount} grid · ${blockCount} blocking cells${symmetric ? " in 180° rotational symmetry" : ""} · ${acrossCount} across and ${downCount} down entries`;

function BoardLayer() {
  const xScale = useXScale("column");
  const yScale = useYScale("row");
  const cell = xScale.bandwidth();
  const left = xScale(columnKeys[0])!;
  const top = yScale(rowKeys[0])!;
  return (
    <g>
      {cells.map((c) => (
        <rect
          key={`cell-${c.r}-${c.c}`}
          x={xScale(columnKeys[c.c])}
          y={yScale(rowKeys[c.r])}
          width={cell}
          height={cell}
          fill={c.entry ? PAPER : INK}
          stroke={RULE}
          strokeWidth={1.5}
        />
      ))}
      {cells
        .filter((c) => c.number !== null)
        .map((c) => (
          <text
            key={`number-${c.r}-${c.c}`}
            x={xScale(columnKeys[c.c])! + cell * 0.09}
            y={yScale(rowKeys[c.r])! + cell * 0.08}
            fontSize={cell * NUMBER_SHARE}
            fontWeight={600}
            fill={INK}
            dominantBaseline="hanging"
          >
            {c.number}
          </text>
        ))}
      {/* Board frame in theme chrome, so edge blocks stay distinct from a dark page */}
      <rect x={left} y={top} width={cell * colCount} height={cell * rowCount} fill="none" stroke={t.inkSoft} strokeWidth={3} />
    </g>
  );
}

export default function Chart() {
  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <ChartsContainer
        width={W}
        height={H - HEADER_H}
        series={[]}
        skipAnimation
        margin={{ top: marginY, bottom: marginY, left: marginX, right: marginX }}
        xAxis={[{ id: "column", scaleType: "band", data: columnKeys, categoryGapRatio: 0, position: "none" }]}
        yAxis={[{ id: "row", scaleType: "band", data: rowKeys, categoryGapRatio: 0, position: "none" }]}
      >
        <BoardLayer />
      </ChartsContainer>
    </Box>
  );
}
