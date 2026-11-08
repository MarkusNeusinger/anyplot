// anyplot.ai
// maze-printable: Printable Maze Puzzle
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// The maze is a print artifact: black walls on white paper in both themes; only the page chrome flips
const PAPER = "#FAF8F1";
const WALL_INK = "#1A1A17";
const START_MARK = "S";
const GOAL_MARK = "G";
const TITLE = "maze-printable · javascript · muix · anyplot.ai";
const TITLE_H = 64;
const CAPTION_H = 48;
const PAGE_MARGIN = 48; // empty page around the maze, px
const WALL_SHARE = 0.075; // interior wall thickness as a share of the cell side
const MIN_WALL_PX = 4;
const BORDER_FACTOR = 1.75; // outer boundary weight relative to an interior wall
const MARK_SHARE = 0.55; // start and goal letters as a share of the cell side
const GOAL_DISC_SHARE = 0.4; // radius of the disc behind the goal letter, share of the cell side
const CARD_PAD_CELLS = 0.75; // paper margin around the outer boundary, in cells

// Data: replace these parameters with your own maze size and seed
const MAZE_WIDTH = 22; // role: width
const MAZE_HEIGHT = 22; // role: height
const SEED = 42; // role: seed

// Plot: reads only the parameters and the constants above
// Randomized depth-first search (recursive backtracker, run iteratively): every carved
// passage links a visited cell to a new one, so the passages form a spanning tree and
// exactly one route joins the start (top-left) and the goal (bottom-right).
const startId = 0;
const goalId = MAZE_WIDTH * MAZE_HEIGHT - 1;
const passages = new Set([]);
const visited = new Set([startId]);
const stack = [startId];
let rngState = SEED | 0; // mulberry32, the browser has no seeded RNG
while (stack.length > 0) {
  const current = stack[stack.length - 1];
  const row = Math.floor(current / MAZE_WIDTH);
  const col = current % MAZE_WIDTH;
  const candidates = [
    row > 0 ? current - MAZE_WIDTH : -1,
    row < MAZE_HEIGHT - 1 ? current + MAZE_WIDTH : -1,
    col > 0 ? current - 1 : -1,
    col < MAZE_WIDTH - 1 ? current + 1 : -1,
  ].filter((id) => id >= 0 && !visited.has(id));
  if (candidates.length === 0) {
    stack.pop();
    continue;
  }
  rngState = (rngState + 0x6d2b79f5) | 0;
  let z = Math.imul(rngState ^ (rngState >>> 15), 1 | rngState);
  z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
  const next = candidates[Math.floor((((z ^ (z >>> 14)) >>> 0) / 4294967296) * candidates.length)];
  passages.add(`${Math.min(current, next)}|${Math.max(current, next)}`);
  visited.add(next);
  stack.push(next);
}

// Length of the one solution route, a difficulty cue for the caption; the route itself stays hidden
const cameFrom = new Map([[startId, startId]]);
const queue = [startId];
for (let head = 0; head < queue.length; head++) {
  const current = queue[head];
  const row = Math.floor(current / MAZE_WIDTH);
  const col = current % MAZE_WIDTH;
  const neighbours = [
    row > 0 ? current - MAZE_WIDTH : -1,
    row < MAZE_HEIGHT - 1 ? current + MAZE_WIDTH : -1,
    col > 0 ? current - 1 : -1,
    col < MAZE_WIDTH - 1 ? current + 1 : -1,
  ];
  for (const next of neighbours) {
    if (next >= 0 && !cameFrom.has(next) && passages.has(`${Math.min(current, next)}|${Math.max(current, next)}`)) {
      cameFrom.set(next, current);
      queue.push(next);
    }
  }
}
let solutionSteps = 0;
for (let node = goalId; node !== startId; node = cameFrom.get(node)) solutionSteps++;

// Interior walls in cell units: every shared edge without a carved passage
const walls = [];
for (let row = 0; row < MAZE_HEIGHT; row++) {
  for (let col = 0; col < MAZE_WIDTH; col++) {
    const id = row * MAZE_WIDTH + col;
    if (col < MAZE_WIDTH - 1 && !passages.has(`${id}|${id + 1}`)) {
      walls.push({ x1: col + 1, y1: row, x2: col + 1, y2: row + 1 });
    }
    if (row < MAZE_HEIGHT - 1 && !passages.has(`${id}|${id + MAZE_WIDTH}`)) {
      walls.push({ x1: col, y1: row + 1, x2: col + 1, y2: row + 1 });
    }
  }
}

const CAPTION = `${MAZE_WIDTH} × ${MAZE_HEIGHT} cells · seed ${SEED} · solution route of ${solutionSteps} steps`;

// Square cells: one cell side in px on both axes, the maze centred on its paper card
function MazeLayer() {
  const { left, top, width, height } = useDrawingArea();
  const cell = Math.min(width / (MAZE_WIDTH + 2 * CARD_PAD_CELLS), height / (MAZE_HEIGHT + 2 * CARD_PAD_CELLS));
  const originX = left + (width - cell * MAZE_WIDTH) / 2;
  const originY = top + (height - cell * MAZE_HEIGHT) / 2;
  const pad = cell * CARD_PAD_CELLS;
  const wallStroke = Math.max(MIN_WALL_PX, cell * WALL_SHARE);

  return (
    <g>
      <rect
        x={originX - pad}
        y={originY - pad}
        width={cell * MAZE_WIDTH + 2 * pad}
        height={cell * MAZE_HEIGHT + 2 * pad}
        fill={PAPER}
        stroke={t.grid}
        strokeWidth={1.5}
        rx={8}
      />
      <rect
        x={originX}
        y={originY}
        width={cell * MAZE_WIDTH}
        height={cell * MAZE_HEIGHT}
        fill="none"
        stroke={WALL_INK}
        strokeWidth={wallStroke * BORDER_FACTOR}
        strokeLinejoin="round"
      />
      {walls.map((w, i) => (
        <line
          key={i}
          x1={originX + w.x1 * cell}
          y1={originY + w.y1 * cell}
          x2={originX + w.x2 * cell}
          y2={originY + w.y2 * cell}
          stroke={WALL_INK}
          strokeWidth={wallStroke}
          strokeLinecap="square"
        />
      ))}
      <text
        x={originX + cell / 2}
        y={originY + cell / 2}
        fontSize={cell * MARK_SHARE}
        fontWeight={700}
        fill={WALL_INK}
        textAnchor="middle"
        dominantBaseline="central"
      >
        {START_MARK}
      </text>
      <circle
        cx={originX + (MAZE_WIDTH - 0.5) * cell}
        cy={originY + (MAZE_HEIGHT - 0.5) * cell}
        r={cell * GOAL_DISC_SHARE}
        fill={t.palette[0]}
      />
      <text
        x={originX + (MAZE_WIDTH - 0.5) * cell}
        y={originY + (MAZE_HEIGHT - 0.5) * cell}
        fontSize={cell * MARK_SHARE}
        fontWeight={700}
        fill={WALL_INK}
        textAnchor="middle"
        dominantBaseline="central"
      >
        {GOAL_MARK}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const mazeSide = Math.min(width, height - TITLE_H - CAPTION_H) - PAGE_MARGIN * 2;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div
        style={{
          height: TITLE_H,
          lineHeight: `${TITLE_H}px`,
          fontSize: 26,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <ChartsContainer
          width={mazeSide}
          height={mazeSide}
          series={[]}
          xAxis={[{ position: "none" }]}
          yAxis={[{ position: "none" }]}
          margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
          skipAnimation
        >
          <MazeLayer />
        </ChartsContainer>
      </div>
      <div style={{ height: CAPTION_H, fontSize: 16, color: t.inkSoft }}>{CAPTION}</div>
    </div>
  );
}
