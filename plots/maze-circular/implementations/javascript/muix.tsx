//# anyplot-orientation: square
// anyplot.ai
// maze-circular: Circular Maze Puzzle
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// The maze itself is a print artifact — "black walls on white background for
// print-friendly output" per spec — so its ink/paper colors stay fixed across
// themes, like the crossword-basic muix implementation does for its grid.
// Only the surrounding page and title follow ANYPLOT_THEME.
const PAPER = "#FAF8F1";
const INK = "#1A1A17";
const GOAL_GREEN = "#009E73";

// --- Deterministic PRNG (mulberry32) — the browser has no seeded RNG --------
function mulberry32(seed) {
  let a = seed;
  return function random() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let z = Math.imul(a ^ (a >>> 15), 1 | a);
    z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(42);

// --- Maze topology: a hub cell + RINGS concentric rings of SECTORS cells ----
const RINGS = 7;
const SECTORS = 12;
const ENTRY_SECTOR = 0;

const adjacency = new Map();
function addEdge(a, b) {
  const key = a < b ? `${a}|${b}` : `${b}|${a}`;
  if (!adjacency.has(a)) adjacency.set(a, []);
  if (!adjacency.has(b)) adjacency.set(b, []);
  adjacency.get(a).push({ to: b, key });
  adjacency.get(b).push({ to: a, key });
}

for (let s = 0; s < SECTORS; s++) addEdge("hub", `1-${s}`);
for (let r = 1; r <= RINGS; r++) {
  for (let s = 0; s < SECTORS; s++) addEdge(`${r}-${s}`, `${r}-${(s + 1) % SECTORS}`);
}
for (let r = 1; r < RINGS; r++) {
  for (let s = 0; s < SECTORS; s++) addEdge(`${r}-${s}`, `${r + 1}-${s}`);
}

// Randomized Prim's algorithm carves a spanning tree over the cell graph.
// A spanning tree has no cycles, so there is exactly one path between the
// hub and any cell — including the entry — which is what "exactly one
// solvable path" requires.
const passageKeys = new Set();
const visited = new Set(["hub"]);
let frontier = adjacency.get("hub").slice();
while (frontier.length > 0) {
  const idx = Math.floor(rand() * frontier.length);
  const edge = frontier[idx];
  frontier.splice(idx, 1);
  if (visited.has(edge.to)) continue;
  visited.add(edge.to);
  passageKeys.add(edge.key);
  adjacency.get(edge.to).forEach((next) => {
    if (!visited.has(next.to)) frontier.push(next);
  });
}

const isPassage = (a, b) => passageKeys.has(a < b ? `${a}|${b}` : `${b}|${a}`);

// --- Polar geometry (unit disc, radius 1 = outer wall) ----------------------
const HUB_R = 1 / (RINGS + 1);
const RING_WIDTH = (1 - HUB_R) / RINGS;
const ringInner = (r) => HUB_R + (r - 1) * RING_WIDTH;
const ringOuter = (r) => HUB_R + r * RING_WIDTH;
const ANGLE_STEP = (2 * Math.PI) / SECTORS;
const angleOf = (s) => -Math.PI / 2 + s * ANGLE_STEP; // sector 0 starts at 12 o'clock

function polar(cx, cy, scale, radius, angle) {
  return [cx + scale * radius * Math.cos(angle), cy + scale * radius * Math.sin(angle)];
}

function arcPath(cx, cy, scale, radius, a0, a1) {
  const [x0, y0] = polar(cx, cy, scale, radius, a0);
  const [x1, y1] = polar(cx, cy, scale, radius, a1);
  const large = a1 - a0 > Math.PI ? 1 : 0;
  return `M ${x0} ${y0} A ${scale * radius} ${scale * radius} 0 ${large} 1 ${x1} ${y1}`;
}

// Draws the whole puzzle as raw SVG paths sized off the chart's own drawing
// area — MUI X owns layout/scaling, the maze geometry is ours.
function MazeMark() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  const halfDim = Math.min(width, height) / 2;
  const scale = halfDim * 0.8;

  const walls = [];

  // Hub <-> ring 1 boundary
  for (let s = 0; s < SECTORS; s++) {
    if (!isPassage("hub", `1-${s}`)) {
      walls.push(arcPath(cx, cy, scale, HUB_R, angleOf(s), angleOf(s + 1)));
    }
  }

  // Sector-divider (circumferential) walls, per ring
  for (let r = 1; r <= RINGS; r++) {
    for (let s = 0; s < SECTORS; s++) {
      const a = `${r}-${s}`;
      const b = `${r}-${(s + 1) % SECTORS}`;
      if (isPassage(a, b)) continue;
      const boundaryAngle = angleOf(s + 1);
      const [x0, y0] = polar(cx, cy, scale, ringInner(r), boundaryAngle);
      const [x1, y1] = polar(cx, cy, scale, ringOuter(r), boundaryAngle);
      walls.push(`M ${x0} ${y0} L ${x1} ${y1}`);
    }
  }

  // Ring-boundary (radial) walls between adjacent rings
  for (let r = 1; r < RINGS; r++) {
    for (let s = 0; s < SECTORS; s++) {
      if (!isPassage(`${r}-${s}`, `${r + 1}-${s}`)) {
        walls.push(arcPath(cx, cy, scale, ringOuter(r), angleOf(s), angleOf(s + 1)));
      }
    }
  }

  // Outer perimeter, with a gap left open at the entry sector
  for (let s = 0; s < SECTORS; s++) {
    if (s === ENTRY_SECTOR) continue;
    walls.push(arcPath(cx, cy, scale, 1, angleOf(s), angleOf(s + 1)));
  }

  const entryMid = angleOf(ENTRY_SECTOR) + ANGLE_STEP / 2;
  const [tickX0, tickY0] = polar(cx, cy, scale, 1, entryMid);
  const [tickX1, tickY1] = polar(cx, cy, scale, 1.06, entryMid);
  const [labelX, labelY] = polar(cx, cy, scale, 1.16, entryMid);

  return (
    <g>
      <rect x={left} y={top} width={width} height={height} fill={PAPER} stroke={INK} strokeWidth={2} />
      {walls.map((d, i) => (
        <path key={i} d={d} fill="none" stroke={INK} strokeWidth={3.5} strokeLinecap="round" />
      ))}
      <line x1={tickX0} y1={tickY0} x2={tickX1} y2={tickY1} stroke={INK} strokeWidth={3.5} strokeLinecap="round" />
      <text x={labelX} y={labelY} fontSize={20} fontWeight={600} fill={INK} textAnchor="middle" dominantBaseline="middle">
        START
      </text>
      <circle cx={cx} cy={cy} r={scale * HUB_R * 0.6} fill={GOAL_GREEN} stroke={PAPER} strokeWidth={2} />
    </g>
  );
}

const TITLE = "maze-circular · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;
  const margin = 48;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: t.ink,
          fontSize: 30,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
          pt: "16px",
          height: TITLE_HEIGHT,
          fontFamily: "inherit",
        }}
      >
        {TITLE}
      </Typography>
      <Box sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <ScatterChart
          width={width}
          height={chartHeight}
          skipAnimation
          disableVoronoi
          series={[{ id: "maze", type: "scatter", data: [{ x: 0, y: 0, id: "c" }] }]}
          xAxis={[{ scaleType: "linear", min: -1.3, max: 1.3, disableTicks: true, disableLine: true }]}
          yAxis={[{ scaleType: "linear", min: -1.3, max: 1.3, disableTicks: true, disableLine: true }]}
          topAxis={null}
          bottomAxis={null}
          leftAxis={null}
          rightAxis={null}
          margin={{ top: margin, bottom: margin, left: margin, right: margin }}
          slots={{ scatter: MazeMark }}
          slotProps={{ legend: { hidden: true } }}
        />
      </Box>
    </Box>
  );
}
