// anyplot.ai
// maze-printable: Printable Maze Puzzle
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Deterministic PRNG (mulberry32) — browser has no seeded Math.random ----
const mulberry32 = (seed) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
  return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
};
const rng = mulberry32(20260905);

// --- Maze generation: randomized depth-first search (recursive backtracker) -
// Guarantees a "perfect maze" — exactly one path between any two cells.
const cols = 22;
const rows = 22;
const cells = Array.from({ length: cols * rows }, () => ({
  top: true,
  right: true,
  bottom: true,
  left: true,
  visited: false,
}));
const index = (col, row) => row * cols + col;

const stack = [{ col: 0, row: 0 }];
cells[index(0, 0)].visited = true;
while (stack.length > 0) {
  const { col, row } = stack[stack.length - 1];
  const candidates = [
    { col, row: row - 1, dir: "top", opp: "bottom" },
    { col: col + 1, row, dir: "right", opp: "left" },
    { col, row: row + 1, dir: "bottom", opp: "top" },
    { col: col - 1, row, dir: "left", opp: "right" },
  ].filter(
    (n) =>
      n.col >= 0 &&
      n.col < cols &&
      n.row >= 0 &&
      n.row < rows &&
      !cells[index(n.col, n.row)].visited,
  );

  if (candidates.length === 0) {
    stack.pop();
    continue;
  }
  const next = candidates[Math.floor(rng() * candidates.length)];
  const current = cells[index(col, row)];
  const neighbor = cells[index(next.col, next.row)];
  current[next.dir] = false;
  neighbor[next.opp] = false;
  neighbor.visited = true;
  stack.push({ col: next.col, row: next.row });
}

// --- Layout -------------------------------------------------------------
const margin = { top: 120, right: 70, bottom: 80, left: 70 };
const availableWidth = width - margin.left - margin.right;
const availableHeight = height - margin.top - margin.bottom;
const cellSize = Math.floor(
  Math.min(availableWidth / cols, availableHeight / rows),
);
const mazeWidth = cellSize * cols;
const mazeHeight = cellSize * rows;
const offsetX = margin.left + (availableWidth - mazeWidth) / 2;
const offsetY = margin.top + (availableHeight - mazeHeight) / 2;

// --- SVG mount ------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg.append("g").attr("transform", `translate(${offsetX},${offsetY})`);

// --- Walls: merge same-direction adjacent segments into fewer path elements
// via d3.path, and give the outer border a heavier stroke than the interior
// walls so the puzzle frame reads as a clear visual hierarchy (DE-01) --------
const innerWallPaths = [];

// Interior horizontal grid lines (between row r-1 and row r), run-length
// encoded with d3.path so a contiguous stretch of wall becomes one subpath.
d3.range(1, rows).forEach((r) => {
  const p = d3.path();
  let runStart = null;
  d3.range(cols + 1).forEach((col) => {
    const hasWall = col < cols && cells[index(col, r - 1)].bottom;
    if (hasWall && runStart === null) runStart = col;
    if (!hasWall && runStart !== null) {
      p.moveTo(runStart * cellSize, r * cellSize);
      p.lineTo(col * cellSize, r * cellSize);
      runStart = null;
    }
  });
  const d = p.toString();
  if (d) innerWallPaths.push(d);
});

// Interior vertical grid lines (between col c-1 and col c), same run-length
// merge along the column.
d3.range(1, cols).forEach((c) => {
  const p = d3.path();
  let runStart = null;
  d3.range(rows + 1).forEach((row) => {
    const hasWall = row < rows && cells[index(c - 1, row)].right;
    if (hasWall && runStart === null) runStart = row;
    if (!hasWall && runStart !== null) {
      p.moveTo(c * cellSize, runStart * cellSize);
      p.lineTo(c * cellSize, row * cellSize);
      runStart = null;
    }
  });
  const d = p.toString();
  if (d) innerWallPaths.push(d);
});

g.selectAll("path.wall-inner")
  .data(innerWallPaths)
  .join("path")
  .attr("class", "wall-inner")
  .attr("d", (d) => d)
  .attr("fill", "none")
  .attr("stroke", t.ink)
  .attr("stroke-width", 3)
  .attr("stroke-linecap", "square");

// Outer border: the maze boundary is always fully closed (the DFS carver
// never removes a perimeter wall), so it renders as a single heavier-stroke
// rectangle that frames the puzzle.
const borderPath = d3.path();
borderPath.moveTo(0, 0);
borderPath.lineTo(mazeWidth, 0);
borderPath.lineTo(mazeWidth, mazeHeight);
borderPath.lineTo(0, mazeHeight);
borderPath.closePath();

g.append("path")
  .attr("class", "wall-border")
  .attr("d", borderPath.toString())
  .attr("fill", "none")
  .attr("stroke", t.ink)
  .attr("stroke-width", 6)
  .attr("stroke-linejoin", "miter");

// --- Start / goal markers ---------------------------------------------------
const markers = [
  { col: 0, row: 0, label: "S", name: "Start", color: t.palette[0] },
  {
    col: cols - 1,
    row: rows - 1,
    label: "G",
    name: "Goal",
    color: t.palette[1],
  },
];

const markerGroup = g
  .selectAll("g.marker")
  .data(markers)
  .join("g")
  .attr("class", "marker")
  .attr(
    "transform",
    (d) =>
      `translate(${d.col * cellSize + cellSize / 2},${d.row * cellSize + cellSize / 2})`,
  );

markerGroup
  .append("circle")
  .attr("r", cellSize * 0.36)
  .attr("fill", (d) => d.color);
markerGroup
  .append("text")
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .attr("fill", t.pageBg)
  .style("font-size", `${Math.round(cellSize * 0.42)}px`)
  .style("font-weight", "700")
  .text((d) => d.label);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("maze-printable · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 88)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text(`${cols} × ${rows} grid · single guaranteed solution path`);

// --- Legend -----------------------------------------------------------------
const legend = svg
  .append("g")
  .attr(
    "transform",
    `translate(${width / 2 - 130},${height - margin.bottom / 2 + 8})`,
  );

const legendItems = legend
  .selectAll("g.legend-item")
  .data(markers)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (_, i) => `translate(${i * 140},0)`);

legendItems
  .append("circle")
  .attr("r", 12)
  .attr("cy", -6)
  .attr("fill", (d) => d.color);
legendItems
  .append("text")
  .attr("x", 22)
  .attr("y", -1)
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => d.name);
