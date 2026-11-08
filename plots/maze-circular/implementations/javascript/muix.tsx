// anyplot.ai
// maze-circular: Circular Maze Puzzle
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// Difficulty sets how often the carve keeps extending the newest passage: a high share gives long
// winding corridors with few branch points (harder), a low one many short branches (easier).
// The carve is a spanning tree either way, so there is exactly one route between any two cells.
const DIFFICULTY_BIAS = { easy: 0.15, medium: 0.55, hard: 0.85 };
const EXTENT = 1.28; // half-width of the square view in outer-wall radii, leaving room for the entry marker
const WALL_W = 3.5; // interior wall stroke in px
const OUTER_WALL_W = 5.5; // the outer boundary is drawn heavier
const GOAL_INK = "#1A1A17"; // the ink with the stronger contrast on the brand green goal disc

// Data: replace this block with your own parameters
const RINGS = 7; // role: rings
const DIFFICULTY = "medium"; // role: difficulty
const SEED = 42; // role: seed
const SECTORS = 12; // role: extra

// Plot: reads only the parameters and the constants above
// Cell graph: a hub at the centre, then RINGS rings of SECTORS cells; each edge is a wall that can be opened
const edges = [];
for (let s = 0; s < SECTORS; s += 1) edges.push({ a: "hub", b: `1-${s}`, key: `h-${s}` });
for (let r = 1; r <= RINGS; r += 1) {
  for (let s = 0; s < SECTORS; s += 1) edges.push({ a: `${r}-${s}`, b: `${r}-${(s + 1) % SECTORS}`, key: `c-${r}-${s}` });
}
for (let r = 1; r < RINGS; r += 1) {
  for (let s = 0; s < SECTORS; s += 1) edges.push({ a: `${r}-${s}`, b: `${r + 1}-${s}`, key: `r-${r}-${s}` });
}
const adjacency = new Map();
edges.forEach((e) => {
  [[e.a, e.b], [e.b, e.a]].forEach(([from, to]) => {
    if (!adjacency.has(from)) adjacency.set(from, []);
    adjacency.get(from).push({ from, to, key: e.key });
  });
});

// Randomised Prim's carve from the hub, biased by difficulty, with a fixed-seed LCG
const bias = DIFFICULTY_BIAS[DIFFICULTY];
const passages = new Set();
const visited = new Set(["hub"]);
const frontier = [...adjacency.get("hub")];
let lastAdded = "hub";
let state = SEED >>> 0;
while (frontier.length > 0) {
  state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
  const continuing = state / 4294967296 < bias ? frontier.filter((e) => e.from === lastAdded) : [];
  const pool = continuing.length > 0 ? continuing : frontier;
  state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
  const edge = pool[Math.floor((state / 4294967296) * pool.length)];
  frontier.splice(frontier.indexOf(edge), 1);
  if (visited.has(edge.to)) continue;
  visited.add(edge.to);
  lastAdded = edge.to;
  passages.add(edge.key);
  adjacency.get(edge.to).forEach((next) => {
    if (!visited.has(next.to)) frontier.push(next);
  });
}

// The entry is the outer cell farthest from the goal along the carved passages
const distance = new Map([["hub", 0]]);
const queue = ["hub"];
while (queue.length > 0) {
  const cell = queue.shift();
  adjacency.get(cell).forEach((e) => {
    if (passages.has(e.key) && !distance.has(e.to)) {
      distance.set(e.to, distance.get(cell) + 1);
      queue.push(e.to);
    }
  });
}
const entrySector = Array.from({ length: SECTORS }, (_, s) => s).reduce(
  (best, s) => (distance.get(`${RINGS}-${s}`) > distance.get(`${RINGS}-${best}`) ? s : best),
  0,
);
const routeCells = distance.get(`${RINGS}-${entrySector}`) + 1;

// Walls in unit-disc geometry: radius 1 is the outer wall, angle 0 points right, sectors run clockwise from 12 o'clock
const HUB_R = 1 / (RINGS + 1);
const RING_W = (1 - HUB_R) / RINGS;
const STEP = (2 * Math.PI) / SECTORS;
const walls = [];
for (let s = 0; s < SECTORS; s += 1) {
  if (!passages.has(`h-${s}`)) walls.push({ arc: true, r: HUB_R, a0: -Math.PI / 2 + s * STEP, width: WALL_W });
}
for (let r = 1; r <= RINGS; r += 1) {
  for (let s = 0; s < SECTORS; s += 1) {
    if (!passages.has(`c-${r}-${s}`)) {
      walls.push({ arc: false, r0: HUB_R + (r - 1) * RING_W, r1: HUB_R + r * RING_W, a0: -Math.PI / 2 + (s + 1) * STEP, width: WALL_W });
    }
    if (r < RINGS && !passages.has(`r-${r}-${s}`)) {
      walls.push({ arc: true, r: HUB_R + r * RING_W, a0: -Math.PI / 2 + s * STEP, width: WALL_W });
    }
  }
}
for (let s = 0; s < SECTORS; s += 1) {
  if (s !== entrySector) walls.push({ arc: true, r: 1, a0: -Math.PI / 2 + s * STEP, width: OUTER_WALL_W });
}
const entryAngle = -Math.PI / 2 + (entrySector + 0.5) * STEP;

const TITLE = "maze-circular · javascript · muix · anyplot.ai";
const SUBTITLE = `${RINGS} rings × ${SECTORS} sectors · ${DIFFICULTY} difficulty · seed ${SEED} · one route of ${routeCells} cells from the entry to the goal`;
const HEADER_H = 80;

function Maze() {
  const xScale = useXScale();
  const yScale = useYScale();
  const unit = xScale(1) - xScale(0);
  const cx = xScale(0);
  const cy = yScale(0);
  const at = (r: number, a: number) => [cx + r * unit * Math.cos(a), cy + r * unit * Math.sin(a)];
  const [tipX, tipY] = at(1.025, entryAngle);
  const [leftX, leftY] = at(1.11, entryAngle - STEP * 0.07);
  const [rightX, rightY] = at(1.11, entryAngle + STEP * 0.07);
  // The label continues outward past the arrow, anchored away from the circle on whichever side the entry lies
  const [labelX, labelY] = at(1.15, entryAngle);
  const labelAnchor = Math.cos(entryAngle) > 0.3 ? "start" : Math.cos(entryAngle) < -0.3 ? "end" : "middle";
  return (
    <g>
      {walls.map((w, i) => {
        const [x0, y0] = at(w.arc ? w.r : w.r0, w.a0);
        const [x1, y1] = w.arc ? at(w.r, w.a0 + STEP) : at(w.r1, w.a0);
        const d = w.arc ? `M ${x0} ${y0} A ${w.r * unit} ${w.r * unit} 0 0 1 ${x1} ${y1}` : `M ${x0} ${y0} L ${x1} ${y1}`;
        return <path key={i} d={d} fill="none" stroke={t.ink} strokeWidth={w.width} strokeLinecap="round" />;
      })}
      <path d={`M ${tipX} ${tipY} L ${leftX} ${leftY} L ${rightX} ${rightY} Z`} fill={t.palette[0]} />
      <text x={labelX} y={labelY} fontSize={18} fontWeight={700} fill={t.ink} textAnchor={labelAnchor} dominantBaseline="middle">
        START
      </text>
      <circle cx={cx} cy={cy} r={HUB_R * unit * 0.62} fill={t.palette[0]} />
      <text x={cx} y={cy} fontSize={14} fontWeight={700} fill={GOAL_INK} textAnchor="middle" dominantBaseline="central">
        GOAL
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const bodyH = height - HEADER_H;
  // Equal px per unit on both axes: the drawing area is the largest centred square
  const side = Math.min(width, bodyH) - 24;
  const margin = { left: (width - side) / 2, right: (width - side) / 2, top: (bodyH - side) / 2, bottom: (bodyH - side) / 2 };

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 40px", boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={bodyH}
        series={[]}
        skipAnimation
        margin={margin}
        xAxis={[{ id: "x", scaleType: "linear", min: -EXTENT, max: EXTENT, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: -EXTENT, max: EXTENT, reverse: true, position: "none" }]}
      >
        <Maze />
      </ChartsContainer>
    </div>
  );
}
