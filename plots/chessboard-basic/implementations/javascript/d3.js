// anyplot.ai
// chessboard-basic: Chess Board Grid Visualization
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-01

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
    const file = files[col];
    const rank = ranks[row];
    squares.push({
      file,
      rank,
      isDark: (col + row) % 2 === 0,
      // h1 and a8 are the light-square corners the spec calls out —
      // flagged here so we can give them a subtle focal accent below.
      isNamedCorner: (file === "h" && rank === "1") || (file === "a" && rank === "8"),
    });
  }
}

// Board colors stay fixed across themes — like a physical board, not
// chrome — only labels and the frame adapt to ANYPLOT_THEME.
const LIGHT_SQUARE = "#EDE0C8";
const DARK_SQUARE = "#8B5A2B";

// --- Layout --------------------------------------------------------------
// A bezel around the board (like a wooden surround under a physical board)
// carries the drop shadow, so the frame itself stays a crisp, classic square.
const margin = { top: 100, right: 50, bottom: 70, left: 70 };
const bezelPad = 26;
const availW = width - margin.left - margin.right;
const availH = height - margin.top - margin.bottom;
const boardSize = Math.min(availW, availH) - bezelPad * 2;
const squareSize = boardSize / 8;
const footprint = boardSize + bezelPad * 2;
const boardLeft = margin.left + (availW - footprint) / 2 + bezelPad;
const boardTop = margin.top + (availH - footprint) / 2 + bezelPad;

// --- Scales -------------------------------------------------------------
// Idiomatic d3 band scales drive square + label placement (rank domain is
// reversed so rank 8 lands at the top), rather than manual index math.
const x = d3.scaleBand().domain(files).range([0, boardSize]);
const y = d3.scaleBand().domain([...ranks].reverse()).range([0, boardSize]);

// --- SVG mount -------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// Soft drop shadow under the board bezel — flood color rides the theme ink
// token, so it reads as a shadow in light mode and a faint glow in dark mode.
const filter = svg.append("defs").append("filter").attr("id", "board-shadow").attr("x", "-40%").attr("y", "-40%").attr("width", "180%").attr("height", "180%");
filter.append("feDropShadow").attr("dx", 0).attr("dy", 10).attr("stdDeviation", 14).attr("flood-color", t.ink).attr("flood-opacity", 0.25);

// --- Bezel (elevated surface the board rests on) ----------------------------
svg
  .append("rect")
  .attr("x", boardLeft - bezelPad)
  .attr("y", boardTop - bezelPad)
  .attr("width", footprint)
  .attr("height", footprint)
  .attr("rx", 18)
  .attr("fill", t.elevatedBg)
  .attr("filter", "url(#board-shadow)");

const board = svg.append("g").attr("transform", `translate(${boardLeft},${boardTop})`);

// --- Squares -----------------------------------------------------------------
board
  .selectAll("rect")
  .data(squares)
  .join("rect")
  .attr("x", (d) => x(d.file))
  .attr("y", (d) => y(d.rank))
  .attr("width", x.bandwidth())
  .attr("height", y.bandwidth())
  .attr("fill", (d) => (d.isDark ? DARK_SQUARE : LIGHT_SQUARE));

// --- Corner accent -------------------------------------------------------
// A subtle amber dot marks h1 and a8, the light-square corners the spec
// calls out — a light storytelling touch without disturbing the classic
// board look.
board
  .selectAll(".corner-accent")
  .data(squares.filter((d) => d.isNamedCorner))
  .join("circle")
  .attr("class", "corner-accent")
  .attr("cx", (d) => x(d.file) + x.bandwidth() / 2)
  .attr("cy", (d) => y(d.rank) + y.bandwidth() / 2)
  .attr("r", squareSize * 0.09)
  .attr("fill", t.amber)
  .attr("opacity", 0.6);

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
  .attr("x", (d) => x(d) + x.bandwidth() / 2)
  .attr("y", boardSize + 34)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "19px")
  .text((d) => d);

// --- Rank labels (1-8, left) -------------------------------------------------
board
  .selectAll(".rank-label")
  .data(ranks)
  .join("text")
  .attr("class", "rank-label")
  .attr("x", -22)
  .attr("y", (d) => y(d) + y.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "19px")
  .text((d) => d);

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "27px")
  .style("font-weight", "600")
  .text("chessboard-basic · javascript · d3 · anyplot.ai");
