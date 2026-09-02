// anyplot.ai
// crossword-basic: Crossword Puzzle Grid
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Updated: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// The block/entry pattern is data (like the Imprint palette), not theme chrome:
// it must render identically in both themes, so these fills are fixed hex
// literals rather than theme-adaptive tokens. Only stroke/frame/title follow
// the theme.
const BLOCK_FILL = "#1A1A17";
const ENTRY_FILL = "#FAF8F1";
const NUMBER_FILL = "#4A4A44";

// --- Data: symmetric 13x13 block pattern (180-degree rotational symmetry) --
// Only the top half (rows 0-6, row 6 is the center row) is authored by hand;
// the bottom half is derived by point-reflection so symmetry is exact by
// construction rather than by manually mirrored coordinates.
const N = 13;
const half = [
  ".....#.#.....",
  ".....#.#.....",
  "##.........##",
  "...#.....#...",
  "......#......",
  ".#.........#.",
  "....#.#.#....",
];
const grid = [];
for (let r = 0; r <= 6; r++) {
  grid[r] = half[r].split("").map((ch) => (ch === "#" ? 1 : 0));
}
for (let r = 7; r < N; r++) {
  grid[r] = grid[N - 1 - r].slice().reverse();
}

// --- Clue numbering: standard newspaper-crossword rule -----------------
// A white cell starts a number if it opens an across run (no white cell to
// its left, a white cell to its right) or a down run (no white cell above,
// a white cell below). Numbers increment in reading order.
const numbers = new Map();
let clueNumber = 1;
for (let r = 0; r < N; r++) {
  for (let c = 0; c < N; c++) {
    if (grid[r][c] === 1) continue;
    const startsAcross =
      (c === 0 || grid[r][c - 1] === 1) && c + 1 < N && grid[r][c + 1] === 0;
    const startsDown =
      (r === 0 || grid[r - 1][c] === 1) && r + 1 < N && grid[r + 1][c] === 0;
    if (startsAcross || startsDown) {
      numbers.set(`${r},${c}`, clueNumber++);
    }
  }
}

// --- Layout -----------------------------------------------------------------
const margin = { top: 120, right: 80, bottom: 40, left: 80 };
const cell = (width - margin.left - margin.right) / N;
const gridX = margin.left;
const gridY = margin.top;

// --- SVG mount ----------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg.append("g").attr("transform", `translate(${gridX},${gridY})`);

// --- Cells: white entry squares, black blocking squares -----------------
const cells = d3.cross(d3.range(N), d3.range(N)).map(([r, c]) => ({
  r,
  c,
  blocked: grid[r][c] === 1,
  number: numbers.get(`${r},${c}`),
}));

g.selectAll("rect.cell")
  .data(cells)
  .join("rect")
  .attr("class", "cell")
  .attr("x", (d) => d.c * cell)
  .attr("y", (d) => d.r * cell)
  .attr("width", cell)
  .attr("height", cell)
  .attr("fill", (d) => (d.blocked ? BLOCK_FILL : ENTRY_FILL))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

// --- Clue numbers, top-left corner of each word-start cell --------------
// Fixed dark fill: numbers always sit on the fixed off-white ENTRY_FILL, so
// the color must not flip to a light tone in the dark theme.
g.selectAll("text.clue")
  .data(cells.filter((d) => d.number !== undefined))
  .join("text")
  .attr("class", "clue")
  .attr("x", (d) => d.c * cell + 5)
  .attr("y", (d) => d.r * cell + 16)
  .attr("fill", NUMBER_FILL)
  .style("font-size", "15px")
  .style("font-family", "sans-serif")
  .text((d) => d.number);

// --- Outer frame --------------------------------------------------------
g.append("rect")
  .attr("x", 0)
  .attr("y", 0)
  .attr("width", N * cell)
  .attr("height", N * cell)
  .attr("fill", "none")
  .attr("stroke", t.ink)
  .attr("stroke-width", 2.5);

// --- Title ----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 62)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .style("font-family", "sans-serif")
  .text("crossword-basic · javascript · d3 · anyplot.ai");
