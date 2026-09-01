// anyplot.ai
// chessboard-basic: Chess Board Grid Visualization
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-01

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data --------------------------------------------------------------
// 8x8 board, algebraic notation: files a-h (left to right), ranks 1-8
// (bottom to top). h1 and a8 are light squares, matching standard
// chess board orientation.
const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
const ranks = ["1", "2", "3", "4", "5", "6", "7", "8"];
const squares = [];
for (let row = 0; row < 8; row++) {
  for (let col = 0; col < 8; col++) {
    squares.push({ col, row, isDark: (col + row) % 2 === 0 });
  }
}

// Board colors stay fixed across themes — like a physical board, not
// chrome — only labels and the frame adapt to ANYPLOT_THEME.
const LIGHT_SQUARE = "#EDE0C8";
const DARK_SQUARE = "#8B5A2B";

// --- Layout --------------------------------------------------------------
const margin = { top: 100, right: 50, bottom: 70, left: 70 };
const availW = width - margin.left - margin.right;
const availH = height - margin.top - margin.bottom;
const boardSize = Math.min(availW, availH);
const squareSize = boardSize / 8;
const boardLeft = margin.left + (availW - boardSize) / 2;
const boardTop = margin.top + (availH - boardSize) / 2;

// --- SVG mount -------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const board = svg.append("g").attr("transform", `translate(${boardLeft},${boardTop})`);

// --- Squares -----------------------------------------------------------------
board
  .selectAll("rect")
  .data(squares)
  .join("rect")
  .attr("x", (d) => d.col * squareSize)
  .attr("y", (d) => (7 - d.row) * squareSize)
  .attr("width", squareSize)
  .attr("height", squareSize)
  .attr("fill", (d) => (d.isDark ? DARK_SQUARE : LIGHT_SQUARE));

// --- Board frame -------------------------------------------------------------
board
  .append("rect")
  .attr("x", 0)
  .attr("y", 0)
  .attr("width", boardSize)
  .attr("height", boardSize)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2);

// --- File labels (a-h, bottom) -------------------------------------------------
board
  .selectAll(".file-label")
  .data(files)
  .join("text")
  .attr("class", "file-label")
  .attr("x", (_, i) => i * squareSize + squareSize / 2)
  .attr("y", boardSize + 34)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .text((d) => d);

// --- Rank labels (1-8, left) -------------------------------------------------
board
  .selectAll(".rank-label")
  .data(ranks)
  .join("text")
  .attr("class", "rank-label")
  .attr("x", -22)
  .attr("y", (_, i) => (7 - i) * squareSize + squareSize / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .text((d) => d);

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("chessboard-basic · javascript · d3 · anyplot.ai");
