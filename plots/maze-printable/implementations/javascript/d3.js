// anyplot.ai
// maze-printable: Printable Maze Puzzle
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

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
    (n) => n.col >= 0 && n.col < cols && n.row >= 0 && n.row < rows && !cells[index(n.col, n.row)].visited
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
const cellSize = Math.floor(Math.min(availableWidth / cols, availableHeight / rows));
const mazeWidth = cellSize * cols;
const mazeHeight = cellSize * rows;
const offsetX = margin.left + (availableWidth - mazeWidth) / 2;
const offsetY = margin.top + (availableHeight - mazeHeight) / 2;

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${offsetX},${offsetY})`);

// --- Walls (print-friendly, consistent thickness, max contrast) -----------
const wallSegments = [];
for (let row = 0; row < rows; row += 1) {
  for (let col = 0; col < cols; col += 1) {
    const cell = cells[index(col, row)];
    const x0 = col * cellSize;
    const y0 = row * cellSize;
    const x1 = x0 + cellSize;
    const y1 = y0 + cellSize;
    if (row === 0 && cell.top) wallSegments.push([x0, y0, x1, y0]);
    if (col === 0 && cell.left) wallSegments.push([x0, y0, x0, y1]);
    if (cell.right) wallSegments.push([x1, y0, x1, y1]);
    if (cell.bottom) wallSegments.push([x0, y1, x1, y1]);
  }
}

g.selectAll("line.wall")
  .data(wallSegments)
  .join("line")
  .attr("class", "wall")
  .attr("x1", (d) => d[0])
  .attr("y1", (d) => d[1])
  .attr("x2", (d) => d[2])
  .attr("y2", (d) => d[3])
  .attr("stroke", t.ink)
  .attr("stroke-width", 4)
  .attr("stroke-linecap", "square");

// --- Start / goal markers ---------------------------------------------------
const markers = [
  { col: 0, row: 0, label: "S", name: "Start", color: t.palette[0] },
  { col: cols - 1, row: rows - 1, label: "G", name: "Goal", color: t.palette[1] },
];

const markerGroup = g
  .selectAll("g.marker")
  .data(markers)
  .join("g")
  .attr("class", "marker")
  .attr(
    "transform",
    (d) => `translate(${d.col * cellSize + cellSize / 2},${d.row * cellSize + cellSize / 2})`
  );

markerGroup.append("circle").attr("r", cellSize * 0.36).attr("fill", (d) => d.color);
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
  .attr("transform", `translate(${width / 2 - 130},${height - margin.bottom / 2 + 8})`);

const legendItems = legend
  .selectAll("g.legend-item")
  .data(markers)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (_, i) => `translate(${i * 140},0)`);

legendItems.append("circle").attr("r", 12).attr("cy", -6).attr("fill", (d) => d.color);
legendItems
  .append("text")
  .attr("x", 22)
  .attr("y", -1)
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => d.name);
