// anyplot.ai
// chessboard-pieces: Chess Board with Pieces for Position Diagrams
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-01

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: Scholar's Mate, final position after 4. Qxf7# --------------------
// Uppercase = white (K/Q/R/B/N/P), lowercase = black (k/q/r/b/n/p).
const pieces = {
  e1: "K",
  a1: "R",
  h1: "R",
  c1: "B",
  c4: "B",
  b1: "N",
  g1: "N",
  f7: "Q",
  a2: "P",
  b2: "P",
  c2: "P",
  d2: "P",
  e4: "P",
  f2: "P",
  g2: "P",
  h2: "P",
  e8: "k",
  d8: "q",
  a8: "r",
  h8: "r",
  c8: "b",
  f8: "b",
  c6: "n",
  f6: "n",
  a7: "p",
  b7: "p",
  c7: "p",
  d7: "p",
  e5: "p",
  g7: "p",
  h7: "p",
};

const GLYPHS = {
  K: "♔",
  Q: "♕",
  R: "♖",
  B: "♗",
  N: "♘",
  P: "♙",
  k: "♚",
  q: "♛",
  r: "♜",
  b: "♝",
  n: "♞",
  p: "♟",
};

// Piece identity (white/black) is fixed across themes, like the game itself —
// only the board and chrome follow ANYPLOT_THEME.
const PIECE_LIGHT = "#F2ECDA";
const PIECE_DARK = "#2A2822";

// --- Layout -------------------------------------------------------------
const margin = { top: 130, right: 60, bottom: 90, left: 90 };
const availW = width - margin.left - margin.right;
const availH = height - margin.top - margin.bottom;
const boardSize = Math.min(availW, availH);
const cell = boardSize / 8;
const boardX = margin.left + (availW - boardSize) / 2;
const boardY = margin.top + (availH - boardSize) / 2;

const files = ["a", "b", "c", "d", "e", "f", "g", "h"];

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const board = svg.append("g").attr("transform", `translate(${boardX},${boardY})`);

// Column/row -> pixel placement via d3-scale bands (rank 8 at the top, rank 1
// at the bottom — white-at-bottom board orientation).
const xScale = d3.scaleBand().domain(d3.range(8)).range([0, boardSize]);
const yScale = d3.scaleBand().domain(d3.range(8)).range([boardSize, 0]);

// --- Squares (light square on h1, per standard chess convention) ----------
// Explicit per-theme board tones (not a pageBg/ink blend) so the light square
// is always the higher-luminance one in both themes. The previous
// `d3.interpolateRgb(t.pageBg, t.ink)` approach inverted in dark mode because
// `t.ink` flips from dark to light between themes, flipping the blend
// direction along with it.
const boardTones =
  t.theme === "dark" ? { light: "#403F38", dark: t.elevatedBg } : { light: t.elevatedBg, dark: "#C9C7C1" };
const squares = [];
for (let row = 0; row < 8; row++) {
  for (let col = 0; col < 8; col++) {
    squares.push({ col, row, light: (col + row) % 2 === 1 });
  }
}

board
  .selectAll("rect.square")
  .data(squares)
  .join("rect")
  .attr("class", "square")
  .attr("x", (d) => xScale(d.col))
  .attr("y", (d) => yScale(d.row))
  .attr("width", xScale.bandwidth())
  .attr("height", yScale.bandwidth())
  .attr("fill", (d) => (d.light ? boardTones.light : boardTones.dark));

board
  .append("rect")
  .attr("x", 0)
  .attr("y", 0)
  .attr("width", boardSize)
  .attr("height", boardSize)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2);

// --- Pieces (white glyphs get a light fill + dark stroke, black glyphs the
// reverse, so identity reads clearly on either square color or theme) ------
const pieceData = Object.entries(pieces).map(([square, code]) => {
  const col = files.indexOf(square[0]);
  const row = Number(square[1]) - 1;
  return { square, code, col, row, isWhite: code === code.toUpperCase() };
});

board
  .selectAll("text.piece")
  .data(pieceData)
  .join("text")
  .attr("class", "piece")
  .attr("x", (d) => xScale(d.col) + xScale.bandwidth() / 2)
  .attr("y", (d) => yScale(d.row) + yScale.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .style("font-family", "'DejaVu Sans', sans-serif")
  .style("font-size", `${cell * 0.72}px`)
  .style("paint-order", "stroke fill")
  .attr("fill", (d) => (d.isWhite ? PIECE_LIGHT : PIECE_DARK))
  .attr("stroke", (d) => (d.isWhite ? PIECE_DARK : PIECE_LIGHT))
  .attr("stroke-width", (d) => (d.isWhite ? cell * 0.02 : cell * 0.015))
  .text((d) => GLYPHS[d.code]);

// --- Coordinate labels (files below, ranks along the left) ----------------
board
  .selectAll("text.file-label")
  .data(files)
  .join("text")
  .attr("class", "file-label")
  .attr("x", (_, i) => xScale(i) + xScale.bandwidth() / 2)
  .attr("y", boardSize + 34)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "20px")
  .text((f) => f);

board
  .selectAll("text.rank-label")
  .data(d3.range(1, 9))
  .join("text")
  .attr("class", "rank-label")
  .attr("x", -26)
  .attr("y", (r) => yScale(r - 1) + yScale.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .attr("fill", t.inkSoft)
  .style("font-size", "20px")
  .text((r) => r);

// --- Title ------------------------------------------------------------------
const title = "Scholar's Mate, Move 4 · chessboard-pieces · javascript · d3 · anyplot.ai";
const titleRatio = title.length > 67 ? 67 / title.length : 1.0;
const titleSize = Math.max(16, Math.round(22 * titleRatio));

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleSize}px`)
  .style("font-weight", "600")
  .text(title);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 88)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .text("White delivers checkmate: 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#");
