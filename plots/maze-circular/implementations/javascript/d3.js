// anyplot.ai
// maze-circular: Circular Maze Puzzle
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Deterministic PRNG (LCG, seed=42) --------------------------------------
let seed = 42;
function rand() {
  seed = (seed * 16807) % 2147483647;
  return (seed - 1) / 2147483646;
}
function randInt(n) {
  return Math.floor(rand() * n);
}

// --- Polar grid: concentric rings, each subdivided into sectors ------------
// Row 0 is the single central cell (the goal). Each outward row roughly
// doubles its sector count whenever the arc length per cell would otherwise
// grow past the radial ring height, keeping cells close to square.
const numRings = 8;
const difficulty = "medium"; // "easy" | "medium" | "hard"

const rows = [[{ r: 0, i: 0 }]];
for (let r = 1; r < numRings; r++) {
  const radius = r / numRings;
  const circumference = 2 * Math.PI * radius;
  const prevCount = rows[r - 1].length;
  const cellWidth = circumference / prevCount;
  const rowHeight = 1 / numRings;
  const ratio = Math.max(1, Math.round(cellWidth / rowHeight));
  const cellCount = prevCount * ratio;
  rows.push(Array.from({ length: cellCount }, (_, i) => ({ r, i })));
}

function parentIndex(r, i) {
  return Math.floor((i * rows[r - 1].length) / rows[r].length);
}

const childrenMap = []; // childrenMap[r][parentIndex] -> [childIndex, ...]
for (let r = 0; r < numRings - 1; r++) {
  const map = Array.from({ length: rows[r].length }, () => []);
  rows[r + 1].forEach((_, i) => map[parentIndex(r + 1, i)].push(i));
  childrenMap.push(map);
}

function cellKey(c) {
  return `${c.r},${c.i}`;
}
function edgeKey(a, b) {
  const ka = cellKey(a);
  const kb = cellKey(b);
  return ka < kb ? `${ka}|${kb}` : `${kb}|${ka}`;
}
function getNeighbors(c) {
  const count = rows[c.r].length;
  const neighbors = [];
  if (count > 1) {
    neighbors.push({ r: c.r, i: (c.i + 1) % count });
    neighbors.push({ r: c.r, i: (c.i - 1 + count) % count });
  }
  if (c.r > 0) neighbors.push({ r: c.r - 1, i: parentIndex(c.r, c.i) });
  if (c.r < numRings - 1) {
    for (const child of childrenMap[c.r][c.i]) neighbors.push({ r: c.r + 1, i: child });
  }
  return neighbors;
}

// --- Maze carving: growing tree over the spanning graph ---------------------
// Always linking to an unvisited cell keeps the result a spanning tree, which
// guarantees exactly one path between the center and any other cell.
const linked = new Set();
function link(a, b) {
  linked.add(edgeKey(a, b));
}
function isLinked(a, b) {
  return linked.has(edgeKey(a, b));
}

function pickFrontierIndex(n) {
  if (difficulty === "hard") return n - 1; // recursive backtracker: long winding corridors
  if (difficulty === "easy") return randInt(n); // Prim's-style: short, branchy dead ends
  return rand() < 0.5 ? n - 1 : randInt(n); // medium: blend of both
}

const visited = new Set([cellKey({ r: 0, i: 0 })]);
const frontier = [{ r: 0, i: 0 }];
while (frontier.length) {
  const idx = pickFrontierIndex(frontier.length);
  const current = frontier[idx];
  const candidates = getNeighbors(current).filter((n) => !visited.has(cellKey(n)));
  if (candidates.length === 0) {
    frontier.splice(idx, 1);
    continue;
  }
  const next = candidates[randInt(candidates.length)];
  link(current, next);
  visited.add(cellKey(next));
  frontier.push(next);
}

const outerRow = numRings - 1;
const entryIndex = randInt(rows[outerRow].length);

// --- Geometry -----------------------------------------------------------
const outerRadius = 500;
const cx = width / 2;
const cy = 620;

function polarPoint(radius, angle) {
  return [Math.sin(angle) * radius, -Math.cos(angle) * radius];
}
function radialWallPath(r0, r1, angle) {
  const [x0, y0] = polarPoint(r0, angle);
  const [x1, y1] = polarPoint(r1, angle);
  return `M${x0},${y0}L${x1},${y1}`;
}
const arcGen = d3.arc();
function ringWallPath(radius, a0, a1) {
  return arcGen({ innerRadius: radius, outerRadius: radius, startAngle: a0, endAngle: a1 });
}

// --- Wall descriptors: collect first, bind with .data().join() -------------
const wallData = [];
for (let r = 0; r < numRings; r++) {
  const count = rows[r].length;
  const angleStep = (2 * Math.PI) / count;
  const rInner = (r / numRings) * outerRadius;
  const rOuter = ((r + 1) / numRings) * outerRadius;

  for (let i = 0; i < count; i++) {
    // Radial wall between cell i and its clockwise neighbor
    if (count > 1) {
      const cw = { r, i: (i + 1) % count };
      if (!isLinked({ r, i }, cw)) {
        wallData.push({ d: radialWallPath(rInner, rOuter, (i + 1) * angleStep) });
      }
    }

    // Outward wall(s): true outer boundary, or the boundary with row r+1
    if (r === outerRow) {
      if (i !== entryIndex) {
        wallData.push({ d: ringWallPath(rOuter, i * angleStep, (i + 1) * angleStep) });
      }
    } else {
      const childCount = rows[r + 1].length;
      const childAngleStep = (2 * Math.PI) / childCount;
      for (const child of childrenMap[r][i]) {
        if (!isLinked({ r, i }, { r: r + 1, i: child })) {
          wallData.push({ d: ringWallPath(rOuter, child * childAngleStep, (child + 1) * childAngleStep) });
        }
      }
    }
  }
}

// --- SVG mount ----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
const walls = g.append("g").attr("fill", "none").attr("stroke", t.ink).attr("stroke-width", 4).attr("stroke-linecap", "round");

walls
  .selectAll("path")
  .data(wallData)
  .join("path")
  .attr("d", (d) => d.d);

// --- Goal marker (center) ------------------------------------------------
g.append("circle").attr("r", 16).attr("fill", t.palette[0]);

// --- Start marker (outer edge gap): bold inward-pointing arrow -------------
// Sized to match the goal marker's visual weight so it still reads at
// mobile-thumbnail scale, per review feedback (the old thin tick vanished).
const entryAngleStep = (2 * Math.PI) / rows[outerRow].length;
const entryAngle = (entryIndex + 0.5) * entryAngleStep;
const arrowBaseRadius = outerRadius + 40;
const arrowTipRadius = outerRadius - 4;
const arrowHalfWidthAngle = 18 / arrowBaseRadius;
const [tipX, tipY] = polarPoint(arrowTipRadius, entryAngle);
const [baseX0, baseY0] = polarPoint(arrowBaseRadius, entryAngle - arrowHalfWidthAngle);
const [baseX1, baseY1] = polarPoint(arrowBaseRadius, entryAngle + arrowHalfWidthAngle);
g.append("path")
  .attr("d", `M${tipX},${tipY}L${baseX0},${baseY0}L${baseX1},${baseY1}Z`)
  .attr("fill", t.palette[0]);

// --- Caption -------------------------------------------------------------
svg
  .append("text")
  .attr("x", cx)
  .attr("y", 1165)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "17px")
  .text(`${numRings - 1} rings · ${difficulty} difficulty · green marks the goal (center) and start (outer edge)`);

// --- Title -----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("maze-circular · javascript · d3 · anyplot.ai");
