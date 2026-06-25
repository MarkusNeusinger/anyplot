// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-25

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Classic sudoku puzzle
const grid = [
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

// Layout: title area at top, centered grid below
const titleAreaH = 80;
const padSide = 75;
const padBottom = 60;
const availW = width - 2 * padSide;
const availH = height - titleAreaH - padBottom;
const cellSize = Math.floor(Math.min(availW, availH) / 9);
const gridSize = cellSize * 9;
const gridLeft = (width - gridSize) / 2;
const gridTop = titleAreaH + (availH - gridSize) / 2;

// SVG mount
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g").attr("transform", `translate(${gridLeft},${gridTop})`);

// Grid background
g.append("rect")
  .attr("width", gridSize).attr("height", gridSize)
  .attr("fill", t.pageBg);

// Grid lines: thin for cells, thick for 3×3 box boundaries
for (let i = 0; i <= 9; i++) {
  const isBox = i % 3 === 0;
  const sw = isBox ? 2.5 : 0.75;
  const stroke = isBox ? t.ink : t.inkSoft;

  g.append("line")
    .attr("x1", i * cellSize).attr("y1", 0)
    .attr("x2", i * cellSize).attr("y2", gridSize)
    .attr("stroke", stroke).attr("stroke-width", sw)
    .attr("stroke-linecap", "square");

  g.append("line")
    .attr("x1", 0).attr("y1", i * cellSize)
    .attr("x2", gridSize).attr("y2", i * cellSize)
    .attr("stroke", stroke).attr("stroke-width", sw)
    .attr("stroke-linecap", "square");
}

// Given numbers (clues) — Imprint palette position 1
const fs = Math.round(cellSize * 0.52);
grid.forEach((row, ri) => {
  row.forEach((val, ci) => {
    if (val !== 0) {
      g.append("text")
        .attr("x", ci * cellSize + cellSize / 2)
        .attr("y", ri * cellSize + cellSize / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("fill", t.palette[0])
        .style("font-size", `${fs}px`)
        .style("font-weight", "700")
        .style("font-family", "Georgia, 'Times New Roman', serif")
        .text(val);
    }
  });
});

// Title
const titleText = "sudoku-basic · javascript · d3 · anyplot.ai";
const n = titleText.length;
const titleSize = n > 67 ? Math.max(Math.round(22 * 67 / n), 14) : 22;

svg.append("text")
  .attr("x", width / 2).attr("y", titleAreaH * 0.55)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleSize}px`)
  .style("font-weight", "600")
  .text(titleText);
